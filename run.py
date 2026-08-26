#!/usr/bin/env python3
"""
run.py — a thin Golden Thread runtime.

    python3 run.py          needs llama-server (default) or ollama

WHAT THIS IS. You talk to a local model. The answer prints first, whole,
on stdout. Python stamps minutes, not meanings, on stderr. Clause text
stays off the prompt unless /withlaw (the whole file, nothing selected).
file: places a file you named, whole, or refuses. Each turn is captured
into a scribe pile.

WHAT THIS IS NOT. Not GTPS-Agent. Not Vessel. Not a selector. Not Layer 2.
Decisions: .grok/piles/golden-thread-build.txt (辻4740).

THREE ACTS (do not merge):
  EXECUTOR       the model, given your question. This is the conversation.
  WHISTLEBLOWER  Python. examine.py. Never a model call. stderr.
  SHAPE          only if you type /shape. Testimony, not the face.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import file_read                                          # noqa: E402
import law as law_module                                  # noqa: E402
import model                                              # noqa: E402
import turn_record                                        # noqa: E402
from examine import (  # noqa: E402
    clock, dial_clock, held_clock, press_clock, probe_clock, probe_same,
)
from pile_io import (                                     # noqa: E402
    PileError, export_selector, keys_of, load_pile, toc_by,
)
from tape import (                                          # noqa: E402
    is_training_loop_line, parse_ask_line, parse_bang_path,
    parse_closed_line, parse_hold_line, parse_revises_line,
    parse_score_place, should_file_sequel, split_tape,
)
import path_stack                                         # noqa: E402
import relied                                             # noqa: E402
import web                                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY_TURNS = int(os.environ.get("GT_HISTORY_TURNS", "6"))


def standing_history_mode():
    """GT_SCORE_HISTORY: none | fold | raw. Default raw (talk). Unknown → none.

    none is lab isolation, not the talk default. Seclusion gate: a face
    that cannot keep a thread is unusable. Unknown stays none so a typo
    does not silently pick a mode.
    """
    raw = os.environ.get("GT_SCORE_HISTORY")
    if raw is None or not str(raw).strip():
        return "raw"
    v = str(raw).strip().lower()
    if v in ("none", "fold", "raw"):
        return v
    return "none"
DEFAULT_STORY = os.path.join(HERE, "piles", "story.txt")

SHAPE_SYSTEM = (
    "You name a resemblance in ordinary sentences.\n"
    "You have a short story of scars, and one turn (a question and an answer).\n"
    "If you see a resemblance to the story, say it plainly.\n"
    "If you see none, say none.\n"
    "Do not ban a word. Do not refuse the answer. Do not score.\n"
    "Do not call this a verdict. You are speech about form.\n"
)

COMMENT_SYSTEM = (
    "You have one record: a question and an answer.\n"
    "In ordinary sentences, say what this record is for.\n"
    "Do not write a tag. Do not compress it into one verb.\n"
    "Do not invent another question. Do not continue the record as another record.\n"
    "If you cannot tell, say so.\n"
)

LOOK_SYSTEM = (
    "You are shown leftover speech, a path the human declared, and the "
    "researched tag sheet for this record's writer.\n"
    "Use those meanings. @act is a doing; @path is a reaching; the two "
    "named empties are not-yet-discerned and ruled-none.\n"
    "Do not walk every key. Do not pick @act or @path from a menu.\n"
    "If no seat in the sheet fits, say so. Invent a witness key only then, "
    "and say you invented it.\n"
    "In ordinary sentences, say whether the leftover still sits on the "
    "declared path, in those meanings.\n"
    "If you cannot tell, say so.\n"
    "Do not score. Do not call this a verdict. Do not continue the leftover "
    "as more questions.\n"
)

INQUIRE_SYSTEM = (
    "You pick one move from the menu. The menu is the only truth.\n"
    "Reply with the number, or STOP. Do not invent a connection.\n"
    "One short reason sentence after the number is allowed.\n"
)

BEARINGS_SYSTEM = (
    "You are shown a deterministic recap of facts the human already asserted.\n"
    "Speak in five short labeled parts: Current bearings; Living thread; "
    "Most recent revision; Outstanding uncertainty; One next question.\n"
    "Reuse the recap's ONE NEXT line for that last part when it names an ask.\n"
    "Do not invent edges. Do not summarise a chain of model guesses. "
    "If the recap is thin, say so.\n"
)

SHEET_SYSTEM = (
    "You are the record's beneath, not the face. You are shown one turn "
    "and the researched tag sheet.\n"
    "Use those meanings. Do not walk every key. Do not pick tags from a "
    "menu. @act is a doing; @path is a reaching.\n"
    "Propose only the seats this turn needs, as lines of the form "
    "@key:hyphenated-value (no spaces).\n"
    "If no seat fits, say so. Invent a witness key only then, and say you "
    "invented it. @ref is salience (this belongs with that), not a menu.\n"
    "Do not score. Do not file. Do not continue as the face.\n"
)

BIND_SYSTEM = (
    "You are the record's binder, not the face, not the clerk.\n"
    "You are shown one face turn (asked and answered), the tag lines\n"
    "proposed for that turn, and the researched tag sheet.\n"
    "\n"
    "@act is a doing that transforms from within. @path is a reaching\n"
    "(a live direction and two real words, or a named empty).\n"
    "The two named empties are not-yet-discerned and ruled-none.\n"
    "Only a person may assert which empty it is.\n"
    "\n"
    "In ordinary sentences, say:\n"
    "- whether each proposed @act still names a doing IN THIS ANSWER,\n"
    "  or is verb-clothing on a subject-label, or is sheet-atmosphere;\n"
    "- whether each proposed @path still reaches FROM THIS ANSWER,\n"
    "  or was borrowed from the sheet and does not touch the answer;\n"
    "- if you cannot tell, say so.\n"
    "\n"
    "Do not score. Do not rank. Do not call this a verdict.\n"
    "Do not file. Do not rewrite the proposal into new @lines\n"
    "unless you explicitly say you are inventing a witness\n"
    "and that the human must still judge it.\n"
    "Do not walk every key. Do not continue as the face.\n"
    "Do not tell the human to keep or to refuse.\n"
)

BIND_ABSENT = "BIND: not spoken this keep — syntactic proposal only"

def _load(path, what):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        raise SystemExit(f"{what} missing at {path} ({e}). Refusing to run.")
    if not text.strip():
        raise SystemExit(f"{what} at {path} is empty. Refusing to run.")
    return text


def _check_grammar_one_line_per_rule(grammar, name="grammar.gbnf"):
    for i, ln in enumerate(grammar.splitlines(), 1):
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if "::=" not in s:
            raise SystemExit(
                f"{name} line {i} continues a rule onto a second line:\n"
                f"  {ln}\nllama.cpp would accept this, return 200, and "
                f"generate UNGOVERNED prose. One rule per line.")


def held_skin_wanted(held_n):
    """Held pair only while holds are live AND GT_HELD_SKIN=1. Default off."""
    return (
        int(held_n or 0) > 0
        and os.environ.get("GT_HELD_SKIN", "") == "1"
    )


def _line_marker(ln):
    """A lone line that is ANSWER_* or [ALL_CAPS]. Not a content detector."""
    s = ln.strip()
    if s in ("ANSWER_START", "ANSWER_END"):
        return s
    if len(s) > 2 and s[0] == "[" and s[-1] == "]":
        inner = s[1:-1]
        if inner and all((c.isupper() or c == "_") for c in inner):
            return s
    return None


def parse_skin(raw):
    """Split a grammar-masked reply. Markers count only alone on a line.
    There is no Whistleblower section. [HELD] is a named seat, not body.
    Any other [ALL_CAPS] marker ends the current section so leftover
    skins cannot leak into the answer."""
    section, seen_exec, seen_held = None, False, False
    body = []
    held = []
    for ln in (raw or "").splitlines():
        tag = _line_marker(ln)
        if tag is not None:
            if tag == "[EXECUTOR]":
                if seen_exec:
                    break
                seen_exec, section = True, "exec"
            elif tag == "[HELD]":
                if seen_held:
                    break
                seen_held, section = True, "held"
            elif tag == "ANSWER_START":
                continue
            else:
                break
            continue
        if section == "exec":
            body.append(ln)
        elif section == "held":
            held.append(ln)
    answer = "\n".join(body).strip()
    held_text = "\n".join(held).strip()
    return answer, not answer, held_text


def parse_file_prefix(msg):
    """file: <path> [question] — the path is the first token after the sigil."""
    if not msg.startswith("file:"):
        return None, msg
    rest = msg[5:].strip()
    if not rest:
        return "", ""
    if rest[0] in "\"'":
        qch = rest[0]
        end = rest.find(qch, 1)
        if end < 0:
            return rest[1:], ""
        return rest[1:end], rest[end + 1:].strip()
    parts = rest.split(None, 1)
    path = parts[0]
    question = parts[1] if len(parts) > 1 else ""
    return path, question


def story_text():
    path = os.environ.get("GT_STORY", DEFAULT_STORY)
    if not os.path.exists(path):
        return "", f"story card missing at {path}"
    try:
        genesis, blocks = load_pile(path)
        del genesis
        bodies = [b["body"].strip() for b in blocks if b.get("body", "").strip()]
        if bodies:
            return "\n\n".join(bodies), path
    except PileError:
        # Python-scribe card or plain text. Not a gForth pile. Place whole.
        pass
    raw = open(path, encoding="utf-8").read()
    if not raw.strip():
        return "", f"story card empty at {path}"
    return raw, path


HELP = """\
  a normal sentence       ask the model. The first answer is what counts.
  hold: testimony         place testimony in stasis. No model call.
  /held                   list active holds
  /release ref reason     release a hold. Reason required. The held block
                          is not edited.
  /probe                  last turn, under all active holds. A measurement,
                          not a second answer. Never the face.
  /probe ref              same, one hold.
  file: path question     put that file into this turn, whole, then ask.
                          You must type the path. Nothing is looked up for you.
  url: URL question       fetch that URL. trafilatura main-text, whole, or
                          refuse. You type the URL. Nothing is chosen for you.
  fetch: URL question     the same sigil as url:
  search: query           place the hit list (title, url, snippet). No page
                          is fetched. Type url: for a page you name.
  html: path question     a saved HTML file, reduced by python scribe
                          capture --html (pandoc). Or refuse.
  !path words             leftover speech is shown and filed. A second
                          span looks at it. Python does not score a match.
  /history                last-N as a derived view for you.
                          Standing default also places it in the face
                          (raw, divider family). GT_SCORE_HISTORY=none is lab.
  /history key:value      the same view, only turns carrying that tag
  ^                       this turn: place a clerk fold of last-N
  ^^                      this turn: place raw last-N (ASKED/ANSWERED)
  /fold                   print a clerk recap of last-N. No model call.
  /fold a b               articulate seats a..b after /forget (asks,
                          revises, isolated). No model. a and b are
                          1-based seats in that list.
  !ask question           open a burning question. Only you close it.
                          Not a hold. Not put in the face window.
  /open                   list open !ask questions.
  !closed n|ref           close an open ask. n is the /open index.
  /revises n|ref          next turn re-frames that turn. Optional
                          rejected:"..." expanded:"..." narrowed:"..."
                          invariant:"..." — those four keys only.
  /inquire a b            walk asserted revises edges backward in
                          seats a..b. One model pick per step from a
                          Python menu. No invented edge.
  /bearings a b           one model call on the /fold a b recap only.
                          Never a chain. Never fed /inquire's speech.
  /reset [reason]         new empty pile. Old pile is kept.
  /forget                 start the next answers fresh. The diary is kept.
  /sequel                 leftover extra speech from the last answer
  /walk                   summon Japanese + gloss on the last turn.
                          Proposed tags are shown and not filed. Slow
                          the first time. Talk does not wait for this.
  /sheet                  propose tags on the last turn (beneath), then
                          bind them to the face answer. Shown, not filed.
  /bind                   bind the last /sheet proposal to the face turn
                          again. Needs /sheet first. Speech, not a verdict.
  /keep                   file the last /sheet proposal you judged. Files
                          the bind speech with it, or names that bind was
                          absent. The clerk copies; it does not invent.
  /comment                ask what the last record is for. Body only.
                          No tag. You are not asked to write one.
  /raw                    the whole unsplit model output
  /model                  which file is loaded on the server
  /withlaw                put ALL 48 clauses in the system prompt this
                          session (file order, nothing selected). Off by
                          default. /law still only lists titles.
  /declared               your declarations, displayed. Never acted on.
  /skin                   grammar mask. llama-server only. Default pair
                          unless GT_HELD_SKIN=1 and a hold is in stasis,
                          then the held pair. Original pair is untouched.
  /dial α | /dial off     contrastive force toward a placed span.
                          Off by default. llama-server only.
  /press strength span    attention bias on file or a hold ref.
                          Larger strength = stronger press toward the
                          span. Off by default. llama-server only.
  /press off              dial and press together: refused.
  /pile                   this diary's path, genesis, and block count.
  /views                  gForth toc on this pile (text driving).
  /law                    titles only. Nothing is selected.
  /shape                  spoken resemblance. Last turn. Not a verdict.
  /shape key:value        the same, a gather you named.
  /help                   this list.
  /exit                   leave. The diary is kept.
"""

HELD_SKIN_LOUD = (
    "── skin: [HELD] seat — GT_HELD_SKIN=1, not the default pair ──"
)
PRIOR_RECORD = (
    "── prior record (diary, last turns, arrival order — not the line just typed) ──"
)
LIVE_MOUTH = "── live mouth (the human's question now) ──"
PRIOR_RECORD_END = (
    "── end of that record (not the line just typed) ──"
)
FOLD_RECORD = (
    "── placed fold (clerk recap of last turns — not the line just typed) ──"
)


def prior_record_slab(blocks):
    """ASKED/ANSWERED of last-N turns. Not a chat wrap. Not @@ headers.

    Each record is closed with PRIOR_RECORD_END (same divider family as
    ── extra speech — /sequel ──). Without that cut, leftover of a prior
    ANSWERED runs into the next ASKED and into the live mouth.
    """
    parts = []
    for b in blocks or []:
        asked = turn_record.field(b["body"], "ASKED")
        answered = turn_record.field(b["body"], "ANSWERED")
        parts.append(
            "ASKED:\n" + (asked or "")
            + "\n\nANSWERED:\n" + (answered or "")
            + "\n" + PRIOR_RECORD_END
        )
    return "\n\n".join(parts)


def fold_recap(genesis, blocks):
    """Clerk minutes of last-N. No model. Not ASKED/ANSWERED chat labels."""
    parts = [FOLD_RECORD]
    if not blocks:
        parts.append("(no turns in the diary window)")
        return "\n".join(parts)
    n = 0
    for b in blocks:
        n += 1
        name = turn_record.traveling_name(genesis, b)
        asked = (turn_record.field(b["body"], "ASKED") or "").strip()
        answered = (turn_record.field(b["body"], "ANSWERED") or "").strip()
        parts.append(
            str(n) + ". " + name + " — asked: " + asked
            + "\n   answered: " + answered
        )
    return "\n".join(parts)


def _parse_span(bits):
    """bits[0] is the command. Need two integers."""
    if len(bits) != 3:
        return 0, 0, "need two seat numbers (1-based, after /forget)"
    try:
        start = int(bits[1])
        end = int(bits[2])
    except ValueError:
        return 0, 0, "seats must be integers"
    if start < 1 or end < start:
        return 0, 0, "range must be 1 <= a <= b"
    return start, end, ""


def _open_asks_slab():
    genesis, asks = turn_record.active_asks()
    if not asks:
        return ""
    lines = [
        "[OPEN ASKS — human, still burning. Not the turn. Not a menu.]"
    ]
    for i, a in enumerate(asks, 1):
        tes = (turn_record.field(a["body"], "ASK") or "").split("\n", 1)[0]
        name = turn_record.traveling_name(genesis, a)
        lines.append(str(i) + ". " + name + "  " + tes)
    return "\n".join(lines)


def _first_int_token(text):
    for tok in (text or "").replace(".", " ").replace(",", " ").split():
        if tok.isdigit():
            return int(tok)
    return None


def _run_inquire(start, end):
    """Asserted edges only. One model pick per step. Never a chain of guesses."""
    recap, err = turn_record.fold_articulate(start, end)
    del recap
    if err:
        return err
    genesis, turns = turn_record.gather_turns(0)
    span = turns[start - 1:end]
    if not span:
        return "inquire: empty span"
    cur = span[-1]
    visited = set()
    trail = ["── inquire (menu picks — asserted edges only) ──"]
    for _step in range(5):
        name = turn_record.traveling_name(genesis, cur)
        if name in visited:
            trail.append("stop: already visited " + name)
            break
        visited.add(name)
        moves = turn_record.inquire_moves(cur)
        if not moves:
            trail.append(name + " — no asserted edge. Honest stop.")
            break
        menu = []
        for i, (kind, ref) in enumerate(moves, 1):
            menu.append(str(i) + ". " + kind + " " + ref)
        user = (
            "Current turn: " + name + "\n"
            "Moves (only these exist):\n" + "\n".join(menu)
            + "\nReply with the number or STOP."
        )
        try:
            speech = model.face(INQUIRE_SYSTEM, user)
        except model.ServerDown as e:
            trail.append("stop: model missed (" + str(e) + ")")
            break
        pick = _first_int_token(speech or "")
        low = (speech or "").strip().lower()
        if low.startswith("stop") or pick is None:
            trail.append("stop: no menu pick.")
            break
        if pick < 1 or pick > len(moves):
            trail.append("stop: pick not on the menu.")
            break
        kind, ref = moves[pick - 1]
        trail.append(name + " --" + kind + "--> " + ref)
        _g, nxt, _n = turn_record.resolve_turn_seat(ref)
        del _g, _n
        if nxt is None:
            trail.append("stop: that ref is not a turn seat in this window.")
            break
        cur = nxt
    return "\n".join(trail)


def history_slab(place_mode, genesis, blocks):
    """Labeled last-N for the face (and for /probe). Empty if not placed."""
    if place_mode not in ("fold", "raw") or not blocks:
        return ""
    if place_mode == "fold":
        return fold_recap(genesis, blocks)
    return PRIOR_RECORD + "\n" + prior_record_slab(blocks)


def score_clock(placed_mode="none", n_keep=0, held_n=0):
    """What entered the face window. FETCHED discipline, not a ranking."""
    mode = placed_mode or "none"
    if mode in ("fold", "raw"):
        hist = mode + "(" + str(int(n_keep)) + ")"
    else:
        hist = "none"
    return "PLACED: " + hist + " · hold(" + str(int(held_n)) + ")"


def window_status():
    """Diary last-N and holds. Last-N enters the face only if placed."""
    genesis, keep = turn_record.gather_turns(HISTORY_TURNS)
    del genesis
    _g, holds = turn_record.active_holds()
    del _g
    stand = standing_history_mode()
    if stand == "none":
        face_line = (
            "face window: holds + placed file/url + the live line. "
            "Last-N off (GT_SCORE_HISTORY=none, lab). ^ fold or ^^ raw this turn."
        )
    else:
        face_line = (
            "face window: holds + placed file/url + last-N ("
            + stand + ", divider family) + the live line. "
            "Lab isolation: GT_SCORE_HISTORY=none. This turn: ^ fold or ^^ raw."
        )
    lines = [
        score_clock(stand, len(keep), len(holds)),
        face_line,
        "diary: " + str(len(keep)) + " turn(s) after last /forget "
        "(cap " + str(HISTORY_TURNS) + "). "
        "/history is that view for you. /forget drops it.",
    ]
    if not keep:
        lines.append("  (diary empty)")
    for b in keep:
        asked = (turn_record.field(b["body"], "ASKED") or "").strip()
        first = asked.splitlines()[0] if asked else "(empty ASKED)"
        if len(first) > 72:
            first = first[:71] + "…"
        lines.append("  ASKED: " + first)
    if holds:
        lines.append(
            "held: " + str(len(holds))
            + " in stasis. /held lists. /release needs a ref and a reason."
        )
    return "\n".join(lines)
DIAL_BOTH_REFUSE = (
    "dial and press together: refused. Two forces at once cannot be attributed."
)
DIAL_NEED_SPAN = "/dial needs something placed to lean on"
PRESS_NEED_SPAN = "/press needs a placed span to put a hand on"
DIAL_NO_APPLY = (
    "── dial: requested, server did not apply — refusing rather than costume ──"
)
PRESS_NO_APPLY = (
    "── press: requested, server did not apply — refusing rather than costume ──"
)


def dial_loud(alpha):
    return (
        "── dialed: α=" + str(alpha)
        + " toward the placed span — a force you set, not a judgment ──"
    )


def press_loud(strength, span):
    return (
        "── pressed: " + str(strength) + " on " + str(span)
        + " — a hand you placed, not a judgment ──"
    )


def parse_dial_cmd(msg):
    """('off', None) | ('on', typed-α) | ('err', reason)."""
    parts = msg.split()
    if len(parts) == 1:
        return "err", "/dial needs α or off."
    if len(parts) != 2:
        return "err", "/dial takes one setting: a number or off."
    arg = parts[1]
    if arg.lower() == "off":
        return "off", None
    try:
        v = float(arg)
    except ValueError:
        return "err", "/dial α must be a number, or off."
    if v < 0:
        return "err", "/dial α must be ≥ 0. 0 is off."
    if v == 0:
        return "off", None
    return "on", arg


def press_pasta_alpha(user_s):
    """Command surface: larger S = stronger press toward the span.
    Server still receives PASTA exclude α = e^{-S} in (0, 1).
    Old /press 0.01 sent α=0.01 (near-maximal). Same force now is S≈4.605.
    Math in the hook is unchanged: bias = log(α) on keys outside the span.
    """
    s = float(user_s)
    if s <= 0:
        return None
    return 2.718281828459045 ** (-s)


def parse_press_cmd(msg):
    """('off', None, None) | ('on', strength, span) | ('err', reason, None)."""
    parts = msg.split()
    if len(parts) == 1:
        return "err", None, "/press needs strength and a span, or off."
    if len(parts) == 2 and parts[1].lower() == "off":
        return "off", None, None
    if len(parts) != 3:
        return "err", None, "/press <strength> <span> or /press off."
    try:
        v = float(parts[1])
    except ValueError:
        return "err", None, "/press strength must be a number."
    if v <= 0:
        return "err", None, "/press strength must be > 0."
    return "on", parts[1], parts[2]


def _stamp_stderr(fetched_from, held_n=0, dial="", press_s="", press_sp=""):
    print(clock(fetched_from), file=sys.stderr)
    print(held_clock(held_n), file=sys.stderr)
    dline = dial_clock(dial)
    if dline:
        print(dline, file=sys.stderr)
    pline = press_clock(press_s, press_sp)
    if pline:
        print(pline, file=sys.stderr)
    sys.stderr.flush()


def _model_path():
    info = model.loaded_model()
    return (info or {}).get("model") or ""


def _relied_line(masses=None, placed=False):
    return relied.clock(
        model.backend(), _model_path(), masses=masses, placed=placed)


def _press_piece(token, named, file_id):
    """Map a /press span token onto one named piece, or None."""
    if not token:
        return None
    if token == "file":
        if not file_id:
            return None
        for n, t in named:
            if n == file_id:
                return n, t
        return None
    for n, t in named:
        if n == token:
            return n, t
    genesis, held, _note = turn_record.resolve_hold_ref(token)
    del _note
    if held is None:
        return None
    name = turn_record.traveling_name(genesis, held)
    for n, t in named:
        if n == name:
            return n, t
    return None


def _relied_payload(full_prompt, named_pieces, last_ids=()):
    """gt_relied request or (None, clock-line). Never all-heads."""
    path = _model_path()
    b = model.backend()
    if b != "llama":
        return None, relied.clock(b, path)
    prof = relied.load_profile(path)
    if prof is None:
        return None, relied.UNPROFILED
    if not prof["heads"]:
        return None, relied.NO_HEADS
    if not named_pieces:
        return None, relied.NONE_PLACED
    spans = relied.spans_for_hook(
        full_prompt, named_pieces,
        lambda s: model.tokenize(s, add_special=False),
        last_ids=last_ids)
    if not spans:
        return None, relied.NONE_PLACED
    return {"heads": prof["heads"], "spans": spans}, None


def _masses_in_order(resp, names):
    got = relied.parse_gt_relied(resp) or {}
    pairs = []
    for name in names:
        if name in got:
            pairs.append((name, got[name]))
    return pairs


PROBE_DIVIDER = "── probe: the weights' rendering under the placed premise (a measurement, not a second opinion) ──"


def _window_refuse(prompt):
    """Named refuse if the face window cannot hold this prompt. Do not POST."""
    info = model.loaded_model()
    ctx = None
    if isinstance(info, dict):
        ctx = info.get("n_ctx")
    try:
        ctx_n = int(ctx or 0)
    except (TypeError, ValueError):
        ctx_n = 0
    if ctx_n <= 0:
        return ""
    try:
        n_prompt = len(model.tokenize(prompt or "", add_special=False))
    except model.ServerDown as e:
        return "could not tokenize the placed prompt (" + str(e) + ")"
    need = n_prompt + int(model.EXECUTOR_MAX_TOKENS)
    if need <= ctx_n:
        return ""
    return (
        "PLACED TEXT WILL NOT FIT the face window: prompt "
        + str(n_prompt) + " tokens + n_predict "
        + str(int(model.EXECUTOR_MAX_TOKENS)) + " vs n_ctx "
        + str(ctx_n) + ". GT_FILE_MAX_BYTES is a file cap, not a context cap. "
        "Place a smaller extract, raise CTX on :8080, or url: a smaller page. "
        "Nothing was asked of the model."
    )


def _file_block(got):
    extra = ""
    red = getattr(got, "reduction", "") or ""
    if red:
        extra = ", " + red
    return (
        f"[THE FILE YOU PLACED — {got.path}, {got.bytes_read} bytes"
        f"{extra}, whole. This is content, not an obligation.]\n\n{got.content}"
    )


def _probe_file_rebuild(turn):
    """Re-read a file: turn's path and check the quoting pin. Named refuse."""
    mouth = turn_record.field(turn["body"], "MOUTH")
    fetched = turn_record.field(turn["body"], "FETCHED")
    if mouth != "file":
        return "", "same-window-verified", ""
    if not fetched or fetched == "(nothing)":
        return "", "", "/probe: file mouth with no FETCHED path."
    pin = turn_record.tag_first(turn, "quoting")
    got, reason = turn_record.verify_placed_pin(fetched, pin)
    if reason:
        return "", "", "/probe: " + reason
    return _file_block(got), "file-repinned:" + fetched, ""


def _hold_banner_text():
    genesis, holds = turn_record.active_holds()
    del genesis
    parts = []
    for h in holds:
        testimony = turn_record.field(h["body"], "HELD")
        parts.append(turn_record.HOLD_BANNER + "\n" + testimony)
    return "\n\n".join(parts), len(holds)


def _sheet_window_refuse(asked="", answered="", extra="", beneath=False):
    """None if the whole sheet fits. Else a named refusal. Never a core."""
    sheet = path_stack.tag_sheet_beneath()
    if beneath:
        if not model.walk_up():
            msg = (
                "SHEET: REFUSED — no beneath server at " + model.WALK
                + ". Start the CPU 2B there. The face was not asked."
            )
            return msg, sheet
        info = model.walk_props()
    else:
        info = model.loaded_model()
    n_ctx = info.get("n_ctx") if isinstance(info, dict) else None
    ok, need, ctx = path_stack.sheet_fits_ctx(
        n_ctx, sheet, asked, answered, extra)
    if ok:
        return None, sheet
    ctx_s = str(ctx) if ctx else "unknown"
    where = "beneath" if beneath else "face"
    msg = (
        "SHEET: REFUSED — the whole tag sheet is "
        + str(len(path_stack.tag_sheet_text()))
        + " chars; " + where + " window n_ctx=" + ctx_s
        + " (need ~" + str(need) + " tokens). "
        + "A live-core is not the sheet. CPU 2B at :8081 with -c 8192 "
        + "holds it. This summons will not amputate the blood."
    )
    return msg, sheet


def summon_look(declared, sequel):
    """Second span on leftover speech. Returns (speech, engine). Never a boolean.

    Dango may add a Japanese reading. Granite always sees the tag sheet —
    researched meanings, not a menu. Python does not score either.
    """
    dango_part = ""
    engine = "granite"
    if path_stack.dango_ready():
        print("LOOK: Dango on leftover speech (slow first time).",
              file=sys.stderr)
        sys.stderr.flush()
        try:
            jp = path_stack.dango_sequel_look(declared, sequel)
            jp = path_stack.first_sentence(
                path_stack.japanese_span(jp) or jp)
            bits = ["DANGO:\n" + (jp or "(no Japanese)")]
            if jp and path_stack.looks_japanese(jp):
                gloss_why = path_stack.gloss_refuse_reason()
                if gloss_why:
                    bits.append("GLOSS: REFUSED — " + gloss_why)
                else:
                    inter, _raw = path_stack.run_gloss(jp)
                    bits.append("GLOSS:\n" + (inter or "(no gloss line)"))
            dango_part = "\n\n".join(bits)
            engine = "dango-then-granite"
        except Exception as e:
            print(f"LOOK: Dango did not answer ({e}).", file=sys.stderr)
            sys.stderr.flush()
            dango_part = f"DANGO: did not answer ({e})"
    refuse, sheet = _sheet_window_refuse(
        declared, sequel, LOOK_SYSTEM, beneath=True)
    if refuse:
        print(refuse, file=sys.stderr)
        body = (dango_part + "\n\n" if dango_part else "") + refuse
        return body, "refused-window"
    user = sheet + "\n\n"
    user += f"[DECLARED PATH]\n{declared}\n\n"
    user += f"[LEFTOVER SPEECH — not the answer]\n{sequel}\n"
    if dango_part:
        user += "\n[JAPANESE READING — another organ, not a verdict]\n"
        user += dango_part + "\n"
    print("LOOK: Granite chat with the tag sheet. Python does not score.",
          file=sys.stderr)
    sys.stderr.flush()
    try:
        speech = model.look(LOOK_SYSTEM, user)
    except model.ServerDown as e:
        body = (dango_part + "\n\n" if dango_part else "")
        return body + f"LOOK did not answer ({e})", "missed"
    if dango_part:
        return dango_part + "\n\nGRANITE:\n" + (speech or "(empty look)"), engine
    return speech or "(empty look)", engine


class Step:
    """One handled line, for the REPL and the optional TUI."""
    def __init__(self, face="", clerk="", quit=False, code=0, tab="", tab_body=""):
        self.face = face
        self.clerk = clerk
        self.quit = quit
        self.code = code
        self.tab = tab
        self.tab_body = tab_body


_SUMMON_TABS = (
    "/walk", "/sheet", "/bind", "/keep", "/comment", "/shape", "/probe",
    "/views", "/history",
    "/fold", "/open", "/inquire", "/bearings", "/reset",
    "/help", "/held", "/sequel", "/raw", "/pile", "/law", "/declared",
    "/model",
)


class Talk:
    """The session. run.py REPL and talk_tui --live share this.
    Does not change the instrument: same stamps, same hook, same pair."""

    def __init__(self):
        self.contract = ""
        self.grammar = ""
        self.contract_held = ""
        self.grammar_held = ""
        self.law = None
        self.turn_n = 0
        self.last_raw = ""
        self.last_turn_id = ""
        self.last_sequel = ""
        self.last_walk = ""
        self.last_proposal = ""
        self.last_bind = ""
        self.last_walk_turn_id = ""
        self.skin_on = False
        self.law_ref = ""
        self.dial_alpha = None
        self.press_strength = None
        self.press_span = None
        self.place_law = False
        self.pending_revises = None

    def boot(self):
        self.contract = _load(os.path.join(HERE, "contract.txt"), "The output contract")
        self.grammar = _load(os.path.join(HERE, "grammar.gbnf"), "The grammar")
        _check_grammar_one_line_per_rule(self.grammar, "grammar.gbnf")
        self.contract_held = _load(
            os.path.join(HERE, "contract_held.txt"),
            "The held-skin contract")
        self.grammar_held = _load(
            os.path.join(HERE, "grammar_held.gbnf"),
            "The held-skin grammar")
        _check_grammar_one_line_per_rule(self.grammar_held, "grammar_held.gbnf")
        self.law = law_module.load()

        if not model.health():
            print("No local model is answering. Start llama-server "
                  f"(preferred, {model.LLAMA}) or `ollama serve` "
                  f"(model {model.OLLAMA_MODEL}). Refusing to pretend.",
                  file=sys.stderr)
            return 1

        info = model.loaded_model()
        self.turn_n, self.last_raw, self.last_turn_id = 0, "", ""
        self.last_sequel, self.last_walk, self.last_proposal = "", "", ""
        self.last_bind = ""
        self.last_walk_turn_id = ""
        self.skin_on = False
        self.law_ref = ""
        self.dial_alpha = None
        self.press_strength = None
        self.press_span = None

        print("You are talking to a local model. Type a question and press Enter.")
        print(f"model: {info.get('model')}")
        self.place_law = os.environ.get("GT_PLACE_LAW", "") == "1"
        print(f"{len(self.law)} clauses are on disk for /law. None is sent unless /withlaw.")
        if self.place_law:
            print("GT_PLACE_LAW=1 — all clauses will be placed, file order.")
        print("To put a document in front of it, type:  file: path/to/file.txt your question")
        print("You must give the path. Nothing is searched or chosen for you.")
        print("url: / fetch: a page you named. search: the hit list, not a page.")
        print("html: a saved HTML file, through python scribe capture --html.")
        print("After each answer: FETCHED says whether a file or page was placed.")
        print("Optional shell: python3 talk_tui.py  (run.py remains the doorway).")
        print("Talk is recorded as you go. You do not write a tag.")
        print("Extra leftover speech is labelled separately. /help lists commands.")
        print("!path files leftover speech and summons a look. Python does not score it.")
        print(f"diary: {turn_record.turns_path()}")
        print(window_status())
        why = path_stack.walk_refuse_reason()
        if why:
            print("/walk is not ready: " + why + ". Talk still works.")
        else:
            print("/walk: beneath translates (disclosed, not the talk face), "
                  "Dango writes movement, then Leipzig. It does not file a tag.")
        print("/comment asks what the last record is for. Body only. No tag.")
        print("/sheet proposes on the last turn then binds on the 2B at :8081 (not the face).")
        print("/bind re-runs that bind. /keep files the proposal you judged, and names bind if it was silent.")

        return 0

    def _bind_after_sheet(self, asked, answered, genesis, last):
        """Second POST on :8081. Proposal already printed. Does not file."""
        proposal = self.last_proposal or ""
        extra = BIND_SYSTEM + "\n" + proposal
        refuse, sheet = _sheet_window_refuse(
            asked, answered, extra, beneath=True)
        if refuse:
            self.last_bind = ""
            print(refuse)
            print("BIND: " + refuse, file=sys.stderr)
            return
        user = sheet + "\n\n"
        user += "[ASKED]\n" + (asked or "") + "\n\n"
        user += "[ANSWERED]\n" + (answered or "") + "\n\n"
        user += "[PROPOSAL]\n" + proposal + "\n"
        turn_id = turn_record.traveling_name(genesis, last)
        if (self.last_walk and self.last_walk_turn_id
                and self.last_walk_turn_id == turn_id):
            user += "\n[WALK — reveal, not a verdict]\n" + self.last_walk + "\n"
        print("BIND: summoned — 2B reads the proposal against the face.",
              file=sys.stderr)
        sys.stderr.flush()
        try:
            speech = model.bind(BIND_SYSTEM, user)
        except model.ServerDown as e:
            self.last_bind = ""
            print("BIND: " + str(e))
            print("BIND: " + str(e), file=sys.stderr)
            return
        self.last_bind = speech or ""
        print()
        print(self.last_bind or "(empty bind)")
        print("BIND: spoken", file=sys.stderr)

    def handle(self, msg):
        if not msg:
            return "loop"
        low = msg.lower()
        if low in ("/exit", "/quit"):
            return "quit"
        if low == "/help":
            print(HELP)
            return "loop"
        if low == "/skin":
            if model.backend() != "llama" and not self.skin_on:
                print("GBNF binds on llama-server. This backend is "
                      f"{model.backend()}. Turning skin ON would be a "
                      "costume, not a constraint. Refusing.")
                return "loop"
            self.skin_on = not self.skin_on
            print(f"skin = {'ON' if self.skin_on else 'OFF'}.")
            return "loop"
        if low == "/dial" or low.startswith("/dial "):
            kind, val = parse_dial_cmd(msg)
            if kind == "err":
                print(val)
                return "loop"
            if kind == "on":
                if model.backend() != "llama":
                    print("the α-dial binds on llama-server. This backend is "
                          f"{model.backend()}. Turning it ON would be a "
                          "costume, not a constraint. Refusing.")
                    return "loop"
                if self.press_strength:
                    print(DIAL_BOTH_REFUSE)
                    return "loop"
                self.dial_alpha = val
                print("dial = ON. α=" + self.dial_alpha + ". Off by default next sitting.")
                return "loop"
            self.dial_alpha = None
            print("dial = OFF.")
            return "loop"
        if low == "/press" or low.startswith("/press "):
            kind, strength, span = parse_press_cmd(msg)
            if kind == "err":
                print(strength if strength else span)
                return "loop"
            if kind == "on":
                if model.backend() != "llama":
                    print("the span-press binds on llama-server. This backend is "
                          f"{model.backend()}. Turning it ON would be a "
                          "costume, not a constraint. Refusing.")
                    return "loop"
                if self.dial_alpha:
                    print(DIAL_BOTH_REFUSE)
                    return "loop"
                self.press_strength = strength
                self.press_span = span
                print("press = ON. " + strength + " on " + span
                      + ". Off by default next sitting.")
                return "loop"
            self.press_strength = None
            self.press_span = None
            print("press = OFF.")
            return "loop"
        if low == "/withlaw":
            self.place_law = not self.place_law
            print("withlaw = ON. All clauses, file order, nothing selected."
                  if self.place_law else
                  "withlaw = OFF. No clause text in the prompt.")
            return "loop"
        if low == "/law":
            print(f"{len(self.law)} clauses in {self.law.source_path}:")
            for c in self.law.clauses:
                print(f"  Clause {c.id:<3} {c.title}")
            print("\nTitles only. /withlaw places the whole file. Nothing is selected.")
            return "loop"
        if low == "/declared":
            if self.law.declared_conditions:
                print(f"Your declarations in {self.law.declared_path}:")
                for d in self.law.declared_conditions:
                    print(f"  {d}")
                print("Displayed. Never acted on.")
            else:
                print(f"No declarations. {self.law.declared_path} is absent or "
                      f"empty. Nothing was assumed.")
            return "loop"
        if low == "/history" or low.startswith("/history "):
            sel = msg.split(None, 1)[1].strip() if " " in msg else ""
            print(turn_record.view_for_model(HISTORY_TURNS, selector=sel)
                  or "(nothing yet)")
            return "loop"
        if low == "/fold" or low.startswith("/fold "):
            bits = msg.split()
            if len(bits) == 1:
                genesis, keep = turn_record.gather_turns(HISTORY_TURNS)
                print(fold_recap(genesis, keep))
                return "loop"
            start, end, err = _parse_span(bits)
            if err:
                print(err)
                return "loop"
            text, ferr = turn_record.fold_articulate(start, end)
            if ferr:
                print(ferr)
                return "loop"
            print(text)
            return "loop"
        if low == "/open":
            genesis, asks = turn_record.active_asks()
            if not asks:
                print("nothing is open.")
                return "loop"
            for i, a in enumerate(asks, 1):
                name = turn_record.traveling_name(genesis, a)
                first = (turn_record.field(a["body"], "ASK") or "").split(
                    "\n", 1)[0]
                print(str(i) + ". " + name + "  " + first)
            return "loop"
        if low == "/reset" or low.startswith("/reset "):
            reason = msg[6:].strip() if len(msg) > 6 else ""
            old = turn_record.turns_path()
            folder, name = os.path.split(old)
            root, ext = os.path.splitext(name)
            stamp = str(int(time.time()))
            new = os.path.join(folder, root + "-reset-" + stamp + (ext or ".pn"))
            try:
                turn_record.record_reset(old, new, reason=reason or "fresh pile")
            except PileError as e:
                print(f"turn pile refused the reset mark: {e}", file=sys.stderr)
                return "loop"
            os.environ["GT_TURN_PILE"] = new
            try:
                turn_record.ensure_session()
            except PileError as e:
                print(f"new pile refused session: {e}", file=sys.stderr)
            self.turn_n = 0
            self.pending_revises = None
            self.last_proposal = ""
            self.last_bind = ""
            self.last_walk_turn_id = ""
            print("reset. old pile kept: " + old)
            print("new pile: " + new)
            return "loop"
        if low == "/revises" or low.startswith("/revises "):
            parsed = parse_revises_line(msg)
            if parsed is None:
                print("/revises needs a turn seat or ref.")
                return "loop"
            tok, notes, err = parsed
            if err:
                print("/revises: " + err)
                return "loop"
            genesis, target, _note = turn_record.resolve_turn_seat(tok)
            if target is None:
                print("/revises: turn missed.")
                return "loop"
            ref = turn_record.traveling_name(genesis, target)
            try:
                turn_record.record_revises_mark(ref, notes)
            except PileError as e:
                print(f"turn pile refused the revises mark: {e}", file=sys.stderr)
                return "loop"
            self.pending_revises = (ref, notes)
            print("revises marked. next turn refs " + ref)
            return "loop"
        if low == "/inquire" or low.startswith("/inquire "):
            bits = msg.split()
            start, end, err = _parse_span(bits)
            if err:
                print("/inquire a b — seats after /forget.")
                return "loop"
            print(_run_inquire(start, end))
            return "loop"
        if low == "/bearings" or low.startswith("/bearings "):
            bits = msg.split()
            start, end, err = _parse_span(bits)
            if err:
                print("/bearings a b — seats after /forget.")
                return "loop"
            recap, ferr = turn_record.fold_articulate(start, end)
            if ferr:
                print(ferr)
                return "loop"
            print(recap)
            print()
            print("── bearings (one call on the recap — not a chain) ──")
            try:
                speech = model.face(BEARINGS_SYSTEM, recap)
            except model.ServerDown as e:
                print("(model missed; the recap above is the whole answer)")
                print(str(e))
                return "loop"
            print(speech or "(empty bearings)")
            return "loop"
        if low == "/sequel":
            print(self.last_sequel or "(no sequel this session)")
            return "loop"
        if low == "/held":
            genesis, holds = turn_record.active_holds()
            if not holds:
                print("nothing is held.")
                return "loop"
            for h in holds:
                name = turn_record.traveling_name(genesis, h)
                first = (turn_record.field(h["body"], "HELD") or "").split(
                    "\n", 1)[0]
                extra = []
                aw = turn_record.tag_first(h, "awaits")
                ds = turn_record.tag_first(h, "dissolves")
                if aw:
                    extra.append("awaits:" + aw)
                if ds:
                    extra.append("dissolves:" + ds)
                line = name + "  " + first
                if extra:
                    line += "  " + " ".join(extra)
                print(line)
            return "loop"
        if low.startswith("/release"):
            bits = msg.split(None, 2)
            if len(bits) < 3:
                print("/release needs a hold ref and a reason.")
                return "loop"
            _cmd, ref_tok, reason = bits
            del _cmd
            genesis, held, note = turn_record.resolve_hold_ref(ref_tok)
            if note:
                print(note, file=sys.stderr)
            if held is None:
                print("/release: not a held block, or the ref missed.")
                return "loop"
            hold_name = turn_record.traveling_name(genesis, held)
            _, active = turn_record.active_holds()
            active_names = [
                turn_record.traveling_name(genesis, h) for h in active]
            # already released if formed not in active
            if hold_name not in active_names and (
                    turn_record._formed_of(held)
                    not in [turn_record._formed_of(h) for h in active]):
                print("/release: already released.")
                return "loop"
            try:
                turn_record.record_release(hold_name, reason)
            except PileError as e:
                print(f"turn pile refused the release: {e}", file=sys.stderr)
                return "loop"
            print("released " + hold_name)
            return "loop"
        if low == "/walk":
            genesis, last = turn_record.last_turn()
            if last is None:
                print("/walk needs a completed turn.")
                return "loop"
            why = path_stack.walk_refuse_reason()
            if why:
                print("PATH: " + why + ". Talk is still recorded.")
                return "loop"
            asked = turn_record.field(last["body"], "ASKED")
            answered = turn_record.field(last["body"], "ANSWERED")
            written_act = turn_record.tag_first(last, "act")
            written_path = turn_record.tag_first(last, "path")
            print("PATH: summoned — beneath translates (not the talk face), "
                  "Dango writes movement, then Leipzig. First time is slow…",
                  file=sys.stderr)
            sys.stderr.flush()
            rep = path_stack.run_stack(
                asked, answered,
                written_act=written_act, written_path=written_path)
            self.last_walk = path_stack.stack_as_walk_text(rep)
            self.last_walk_turn_id = turn_record.traveling_name(genesis, last)
            print()
            print(self.last_walk)
            try:
                turn_record.record_walk(
                    self.last_walk, [], [],
                    ref_id=turn_record.traveling_name(genesis, last))
            except PileError as e:
                print(f"turn pile refused the walk block: {e}", file=sys.stderr)
            return "loop"
        if low == "/sheet":
            genesis, last = turn_record.last_turn()
            if last is None:
                print("/sheet needs a completed turn.")
                return "loop"
            asked = turn_record.field(last["body"], "ASKED")
            answered = turn_record.field(last["body"], "ANSWERED")
            refuse, sheet = _sheet_window_refuse(
                asked, answered, SHEET_SYSTEM, beneath=True)
            if refuse:
                print(refuse)
                self.last_proposal = ""
                self.last_bind = ""
                return "loop"
            user = sheet + "\n\n"
            user += "[THIS TURN — not the face]\n"
            user += "ASKED:\n" + (asked or "") + "\n\n"
            user += "ANSWERED:\n" + (answered or "") + "\n"
            ask_slab = _open_asks_slab()
            if ask_slab:
                user += "\n" + ask_slab + "\n"
            print("SHEET: summoned — tag sheet on this turn. Not the face.",
                  file=sys.stderr)
            sys.stderr.flush()
            try:
                speech = model.sheet(SHEET_SYSTEM, user)
            except model.ServerDown as e:
                print("SHEET did not answer (" + str(e) + ")")
                return "loop"
            self.last_proposal = speech or ""
            print()
            print(speech or "(empty sheet)")
            print("SHEET: shown, not filed.", file=sys.stderr)
            self._bind_after_sheet(asked, answered, genesis, last)
            return "loop"
        if low == "/bind":
            if not (self.last_proposal or "").strip():
                print("/bind needs a /sheet proposal first.")
                return "loop"
            genesis, last = turn_record.last_turn()
            if last is None:
                print("/bind needs a completed turn.")
                return "loop"
            asked = turn_record.field(last["body"], "ASKED")
            answered = turn_record.field(last["body"], "ANSWERED")
            self._bind_after_sheet(asked, answered, genesis, last)
            return "loop"
        if low == "/keep":
            if not (self.last_proposal or "").strip():
                print("/keep needs a /sheet proposal first.")
                return "loop"
            if (os.environ.get("GT_BIND_REQUIRED") or "").strip() == "1":
                if not (self.last_bind or "").strip():
                    print("KEEP: REFUSED — bind has not spoken (GT_BIND_REQUIRED=1).")
                    return "loop"
            genesis, last = turn_record.last_turn()
            if last is None:
                print("/keep needs a completed turn.")
                return "loop"
            accepted, refused = path_stack.parse_proposal(self.last_proposal)
            print()
            if accepted:
                print("KEEP: filing " + str(len(accepted)) + " tag(s) you judged.")
            else:
                print("KEEP: no @key:value lines accepted.")
            if refused:
                print("KEEP refused: " + "; ".join(refused))
            ref_id = turn_record.traveling_name(genesis, last)
            bind_speech = (self.last_bind or "").strip()
            if bind_speech:
                print("KEEP: proposal filed · BIND spoken")
            else:
                bind_speech = BIND_ABSENT
                print("KEEP: proposal filed · BIND absent")
            try:
                turn_record.record_sheet(
                    self.last_proposal, accepted, refused, ref_id=ref_id)
                turn_record.record_bind(bind_speech, ref_id=ref_id)
            except PileError as e:
                print(f"turn pile refused the sheet keep: {e}", file=sys.stderr)
            self.last_proposal = ""
            self.last_bind = ""
            return "loop"
        if low == "/comment":
            genesis, last = turn_record.last_turn()
            if last is None:
                print("/comment needs a completed turn.")
                return "loop"
            asked = turn_record.field(last["body"], "ASKED")
            answered = turn_record.field(last["body"], "ANSWERED")
            fetched = turn_record.field(last["body"], "FETCHED")
            user = (
                f"[THIS RECORD]\n"
                f"asked: {asked}\n"
                f"answered: {answered}\n"
                f"fetched: {fetched or '(nothing)'}\n"
            )
            try:
                speech = model.comment(COMMENT_SYSTEM, user)
            except model.ServerDown as e:
                print(f"\n{e}")
                return "loop"
            print()
            print("── comment (what this record is for — not a tag) ──")
            print(speech)
            try:
                turn_record.record_comment(
                    speech,
                    ref_id=turn_record.traveling_name(genesis, last))
            except PileError as e:
                print(f"turn pile refused the comment block: {e}",
                      file=sys.stderr)
            return "loop"
        if low == "/probe" or low.startswith("/probe "):
            genesis, last = turn_record.last_turn()
            if last is None:
                print("/probe needs a completed turn.")
                return "loop"
            ref_tok = ""
            if " " in msg:
                ref_tok = msg.split(None, 1)[1].strip()
            _g, holds, refuse = turn_record.holds_for_probe(ref_tok)
            del _g
            if refuse == "nothing is held.":
                print("/probe: nothing is held.")
                return "loop"
            if refuse == "not an active hold.":
                print("/probe: not an active hold.")
                return "loop"
            if refuse:
                print("/probe: " + refuse)
                return "loop"
            file_block, stamp, file_refuse = _probe_file_rebuild(last)
            if file_refuse:
                print(file_refuse)
                return "loop"
            asked = turn_record.field(last["body"], "ASKED")
            answered = turn_record.field(last["body"], "ANSWERED")
            premise_body = turn_record.build_premise_body(holds)
            premise_prompt = turn_record.build_premise_prompt(holds)
            stand = standing_history_mode()
            _hg, prior = turn_record.gather_turns_before(
                last, HISTORY_TURNS)
            del _hg
            if stand == "none":
                prior = []
            user_prompt = asked
            if file_block:
                user_prompt = file_block + "\n\n" + user_prompt
            slab = history_slab(stand, genesis, prior)
            if slab:
                user_prompt = (
                    slab + "\n\n" + LIVE_MOUTH + "\n" + user_prompt
                )
            user_prompt = premise_prompt + "\n\n" + user_prompt
            probe_full = model.granite_chat(user_prompt, None)
            named = []
            for h in holds:
                tes = turn_record.field(h["body"], "HELD")
                name = turn_record.traveling_name(genesis, h)
                if tes:
                    named.append((name, tes))
            payload, pre_clock = _relied_payload(probe_full, named)
            try:
                rendered, probe_resp = model.probe_measured(
                    user_prompt, history_pairs=None, gt_relied=payload)
            except model.ServerDown as e:
                print(f"\n{e}")
                return "loop"
            rendered = rendered or ""
            print()
            print(PROBE_DIVIDER)
            print(rendered)
            identical = probe_same(rendered, answered)
            print(probe_clock(identical), file=sys.stderr)
            names = [n for n, _ in named]
            masses = _masses_in_order(probe_resp, names)
            if payload and probe_resp.get("gt_relied_saw_softmax") is False:
                print(relied.NO_HOOK, file=sys.stderr)
                masses = []
            elif masses:
                print(relied.masses_clock(masses), file=sys.stderr)
            else:
                print(pre_clock or _relied_line(placed=bool(named)),
                      file=sys.stderr)
            sys.stderr.flush()
            turn_name = turn_record.traveling_name(genesis, last)
            hold_names = [
                turn_record.traveling_name(genesis, h) for h in holds]
            try:
                turn_record.record_probe(
                    asked, premise_body, rendered, stamp,
                    turn_ref=turn_name, hold_refs=hold_names,
                    relied=masses)
            except PileError as e:
                print(f"turn pile refused the probe block: {e}",
                      file=sys.stderr)
            return "loop"
        if low == "/forget":
            genesis, turns = turn_record.gather_turns(0)
            del genesis
            n = len(turns)
            try:
                turn_record.record_forget(n)
            except PileError as e:
                print(f"turn pile refused: {e}", file=sys.stderr)
                return "loop"
            print(f"dropped {n} turn(s) from the next model window. "
                  f"The pile was not rewritten.")
            print(window_status())
            return "loop"
        if low == "/pile":
            path = turn_record.turns_path()
            genesis, blocks = load_pile(path)
            print(f"  path: {path}")
            print(f"  genesis: {genesis or '(not linkable yet — no turn written)'}")
            print(f"  blocks: {len(blocks)}")
            print("  /forget drops the model window, not this file.")
            print("  /views runs gForth toc on this pile (text driving).")
            return "loop"
        if low == "/views":
            path = turn_record.turns_path()
            if not os.path.exists(path):
                print("no turn pile yet")
                return "loop"
            print()
            try:
                print(keys_of(path))
            except PileError as e:
                print(f"/views keys: {e}")
            for key in ("act", "path", "part", "refuses", "origin"):
                print()
                try:
                    print(toc_by(path, key))
                except PileError as e:
                    print(f"/views toc {key}: {e}")
            return "loop"
        if low == "/model":
            info = model.loaded_model()
            for k, v in info.items():
                print(f"  {k}: {v}")
            print("  Asked of the server. A model cannot verify itself.")
            return "loop"
        if low == "/raw":
            print(self.last_raw or "(no turn yet)")
            return "loop"
        if low == "/shape" or low.startswith("/shape "):
            selector = msg.split(None, 1)[1].strip() if " " in msg else ""
            card, card_path = story_text()
            if not card:
                print(f"/shape: {card_path}")
                return "loop"
            last_id = ""
            if selector:
                try:
                    slab = export_selector(turn_record.turns_path(), selector)
                except PileError as e:
                    print(f"/shape: {e}")
                    return "loop"
                user = (
                    f"[STORY CARD — {card_path}. Editable. Not the 48 clauses.]\n"
                    f"{card}\n\n"
                    f"[GATHER YOU NAMED — {selector}. "
                    f"scribe export, joined. This is not the pile.]\n"
                    f"{slab}\n"
                )
            else:
                genesis, last = turn_record.last_turn()
                if last is None:
                    print("/shape needs a completed turn, or /shape key:value.")
                    return "loop"
                last_id = turn_record.traveling_name(genesis, last)
                asked = turn_record.field(last["body"], "ASKED")
                answered = turn_record.field(last["body"], "ANSWERED")
                user = (
                    f"[STORY CARD — {card_path}. Editable. Not the 48 clauses.]\n"
                    f"{card}\n\n"
                    f"[THIS TURN]\nasked: {asked}\nanswered: {answered}\n"
                )
            try:
                speech = model.shape(SHAPE_SYSTEM, user)
            except model.ServerDown as e:
                print(f"\n{e}")
                return "loop"
            print()
            print("── shape, spoken (testimony — not a verdict) ──")
            print(speech)
            try:
                turn_record.record_shape(
                    speech, ref_id=last_id, story_path=card_path)
            except PileError as e:
                print(f"turn pile refused the shape block: {e}", file=sys.stderr)
            _stamp_stderr(card_path, _hold_banner_text()[1])
            return "loop"
        if msg.startswith("/"):
            print(f"unknown command {msg.split()[0]} — /help lists them.")
            return "loop"

        ask_q = parse_ask_line(msg)
        if ask_q is not None:
            if not ask_q:
                print("!ask needs a question. Nothing was opened.")
                return "loop"
            try:
                token, _g = turn_record.record_ask(ask_q)
            except PileError as e:
                print(f"turn pile refused the ask: {e}", file=sys.stderr)
                return "loop"
            print("ask open " + token)
            return "loop"
        closed_tok = parse_closed_line(msg)
        if closed_tok is not None:
            if not closed_tok:
                print("!closed needs an /open index or a ref.")
                return "loop"
            genesis, ask, _n = turn_record.resolve_ask_ref(closed_tok)
            if ask is None:
                print("!closed: not an open ask.")
                return "loop"
            name = turn_record.traveling_name(genesis, ask)
            try:
                turn_record.record_ask_closed(name, "closed by hand")
            except PileError as e:
                print(f"turn pile refused the close: {e}", file=sys.stderr)
                return "loop"
            print("ask closed " + name)
            return "loop"

        held_line = parse_hold_line(msg)
        if held_line is not None:
            testimony, awaits, dissolves = held_line
            if not testimony:
                print("hold: needs testimony. Nothing was held.")
                return "loop"
            try:
                token, _gen = turn_record.record_hold(
                    testimony, awaits=awaits, dissolves=dissolves)
            except PileError as e:
                print(f"turn pile refused the hold: {e}", file=sys.stderr)
                return "loop"
            print("held " + token)
            return "loop"

        placed_path, question = parse_file_prefix(msg)
        fetched_from = ""
        delivered = {}
        file_block = ""
        mouth = "bare"
        if placed_path is not None:
            mouth = "file"
            if placed_path == "":
                print("file: needs a path. Nothing was read.")
                return "loop"
            got = file_read.read_placed(placed_path)
            if not got.ok:
                print(f"file: REFUSED {got.path or placed_path} — {got.refused}")
                try:
                    turn_record.record_file_refused(
                        got.path or placed_path, got.refused)
                except PileError as e:
                    print(f"turn pile refused: {e}", file=sys.stderr)
                return "loop"
            fetched_from = got.path
            delivered[f"file: {got.path}"] = got.content
            file_block = _file_block(got)
            if got.refused:
                print(f"(note: {got.refused})")
            question = question or "I placed the file above. Read it."
        if placed_path is None:
            url, question_u = web.parse_url_prefix(msg)
            if url is not None:
                mouth = "fetch"
                if url == "":
                    print("url: needs a URL. Nothing was fetched.")
                    return "loop"
                got = web.fetch_placed(url)
                if not got.ok:
                    print("url: REFUSED " + (got.target or url)
                          + " — " + got.refused)
                    try:
                        turn_record.record_place_refused(
                            "refuse-fetch", "url:", got.target or url,
                            got.refused)
                    except PileError as e:
                        print(f"turn pile refused: {e}", file=sys.stderr)
                    return "loop"
                fetched_from = got.target
                delivered["url: " + got.target] = got.content
                file_block = web.page_block(got)
                question = question_u or "I placed the page above. Read it."
                placed_path = got.target
        if placed_path is None:
            query, question_s = web.parse_search_prefix(msg)
            if query is not None:
                mouth = "search"
                if query == "":
                    print("search: needs a query. Nothing was searched.")
                    return "loop"
                got = web.list_hits(query)
                if not got.ok:
                    print("search: REFUSED " + (got.target or query)
                          + " — " + got.refused)
                    try:
                        turn_record.record_place_refused(
                            "refuse-search", "search:", got.target or query,
                            got.refused)
                    except PileError as e:
                        print(f"turn pile refused: {e}", file=sys.stderr)
                    return "loop"
                fetched_from = "search:" + got.target
                delivered["search: " + got.target] = got.content
                file_block = web.hits_block(got)
                question = question_s or got.target
                placed_path = got.target
                print()
                print(got.content)
                print()
                print("(hit list placed — type url: a page you name)")
        if placed_path is None:
            html_path, question_h = web.parse_html_prefix(msg)
            if html_path is not None:
                mouth = "html"
                if html_path == "":
                    print("html: needs a path. Nothing was read.")
                    return "loop"
                got = web.html_placed(html_path)
                if not got.ok:
                    print("html: REFUSED " + (got.target or html_path)
                          + " — " + got.refused)
                    try:
                        turn_record.record_place_refused(
                            "refuse-html", "html:", got.target or html_path,
                            got.refused)
                    except PileError as e:
                        print(f"turn pile refused: {e}", file=sys.stderr)
                    return "loop"
                fetched_from = got.target
                delivered["html: " + got.target] = got.content
                file_block = web.html_block(got)
                question = question_h or "I placed the HTML above. Read it."
                placed_path = got.target

        user_q = question if placed_path is not None else msg
        sigil, user_q = parse_score_place(user_q)
        stand = standing_history_mode()
        place_mode = sigil if sigil else stand
        if place_mode == "none":
            place_mode = None
        declared, _ = parse_bang_path(msg)
        self.turn_n += 1
        genesis, keep = turn_record.gather_turns(HISTORY_TURNS)
        user_prompt = user_q
        if file_block:
            user_prompt = f"{file_block}\n\n{user_q}"
        banners, held_n = _hold_banner_text()
        hold_genesis, hold_blocks = turn_record.active_holds()
        hold_refs = [
            turn_record.traveling_name(hold_genesis, h) for h in hold_blocks]
        if banners:
            user_prompt = banners + "\n\n" + user_prompt

        use_held_skin = self.skin_on and held_skin_wanted(held_n)
        if use_held_skin:
            system = self.contract_held
        elif self.skin_on:
            system = self.contract
        elif self.place_law:
            system = law_module.law_text(self.law)
        else:
            system = ""
        named = []
        for h, href in zip(hold_blocks, hold_refs):
            tes = turn_record.field(h["body"], "HELD")
            named.append((href, turn_record.HOLD_BANNER + "\n" + tes))
        # C1: his own words are a named span. The most-placed material in any
        # window, and the one thing RELIED could not see until now. Located at
        # its LAST occurrence: the live line sits last in the face window, and
        # a placed file quoting the question back must not capture the span.
        if (user_q or "").strip():
            named.append((relied.ASKED_SPAN, user_q))
        fetched_text = ""
        file_id = ""
        if fetched_from and delivered:
            for _k, _v in delivered.items():
                fetched_text = _v
                break
        if file_block and fetched_from:
            try:
                file_id, _g = turn_record.record_placed_file(
                    fetched_from, fetched_text)
                del _g
                named.append((file_id, file_block))
            except PileError as e:
                print(f"turn pile refused the placed file: {e}",
                      file=sys.stderr)
        if self.place_law and not self.skin_on and system:
            if not self.law_ref:
                try:
                    self.law_ref, _g = turn_record.record_law_text(system)
                    del _g
                except PileError as e:
                    print(f"turn pile refused the law block: {e}",
                          file=sys.stderr)
            if self.law_ref:
                named.append((self.law_ref, system))
        # R1/R2: last-N enters only when he places it. Skin keeps no history.
        if place_mode in ("fold", "raw") and self.skin_on:
            print("PLACED: none — skin is on; fold/raw not placed",
                  file=sys.stderr)
            place_mode = None
        if place_mode in ("fold", "raw") and keep:
            slab = history_slab(place_mode, genesis, keep)
            user_prompt = (
                slab + "\n\n" + LIVE_MOUTH + "\n" + user_prompt
            )
        elif place_mode in ("fold", "raw") and not keep:
            place_mode = None
        hist = None
        gram = None
        if use_held_skin:
            gram = self.grammar_held
        elif self.skin_on:
            gram = self.grammar
        full_prompt = model.executor_prompt(
            system, user_prompt, history_pairs=hist, grammar=gram)
        if file_block:
            print(file_block.split("\n", 1)[0])
        wont = _window_refuse(full_prompt)
        if wont:
            print(wont)
            self.turn_n -= 1
            return "loop"
        if self.dial_alpha and self.press_strength:
            print(DIAL_BOTH_REFUSE)
            self.turn_n -= 1
            return "loop"
        if self.dial_alpha and not named:
            print(DIAL_NEED_SPAN)
            self.turn_n -= 1
            return "loop"
        press_piece = None
        if self.press_strength:
            press_piece = _press_piece(self.press_span, named, file_id)
            if press_piece is None:
                print(PRESS_NEED_SPAN)
                self.turn_n -= 1
                return "loop"
        asked_last = (relied.ASKED_SPAN,)
        payload, pre_clock = _relied_payload(
            full_prompt, named, last_ids=asked_last)
        gt_dial = None
        gt_press = None
        if self.dial_alpha:
            spans = None
            if payload:
                spans = payload.get("spans")
            else:
                spans = relied.spans_for_hook(
                    full_prompt, named,
                    lambda s: model.tokenize(s, add_special=False),
                    last_ids=asked_last)
            if not spans:
                print(DIAL_NEED_SPAN)
                self.turn_n -= 1
                return "loop"
            gt_dial = {"alpha": float(self.dial_alpha), "spans": spans}
        if self.press_strength and press_piece:
            path = _model_path()
            prof = relied.load_profile(path)
            if prof is None or not prof.get("heads"):
                print("/press needs a head profile (4a reuse is a "
                      "hypothesis; unprofiled — refusing rather than "
                      "all-heads).")
                self.turn_n -= 1
                return "loop"
            one = [press_piece]
            spans = relied.spans_for_hook(
                full_prompt, one,
                lambda s: model.tokenize(s, add_special=False))
            if not spans:
                print(PRESS_NEED_SPAN)
                self.turn_n -= 1
                return "loop"
            n_prompt = len(model.tokenize(full_prompt, add_special=False))
            pasta_a = press_pasta_alpha(self.press_strength)
            if pasta_a is None:
                print("/press strength must be > 0.")
                self.turn_n -= 1
                return "loop"
            gt_press = {
                "strength": pasta_a,
                "n_prompt": n_prompt,
                "heads": prof["heads"],
                "spans": spans,
            }
        try:
            raw, resp = model.executor_measured(
                system, user_prompt, grammar=gram,
                history_pairs=hist, gt_relied=payload,
                gt_dial=gt_dial, gt_press=gt_press,
                seed=0 if (payload or gt_dial or gt_press) else None)
        except model.ServerDown as e:
            print(f"\n{e}")
            self.turn_n -= 1
            return "loop"
        self.last_raw = raw

        cut_byte = None
        if self.skin_on:
            answer, absent, _held_seat = parse_skin(raw)
            del _held_seat
            sequel = ""
        else:
            answer, sequel, cut_byte = split_tape(raw, asked=user_q)
            if answer and is_training_loop_line(answer.splitlines()[0]):
                sequel = (answer + "\n" + sequel).strip()
                answer = ""
            absent = not answer

        # C3: the underside curve. The hook was cut-ignorant; the cut arrives
        # here. A series that does not reconcile with the generation is refused,
        # never walked to a quietly misplaced boundary. Disclosure only: no
        # curve is ever a gate, a filter, a selector, or a cut.
        underside_line = ""
        underside_profiles = None
        underside_series = None
        underside_refusal = ""
        if not use_held_skin:
            _ser, _snote = relied.parse_series(resp)
            underside_series = _ser
            if _ser is not None:
                underside_profiles, _pnote = relied.split_series(
                    _ser, cut_byte, len((raw or "").encode("utf-8")))
                if underside_profiles is not None:
                    underside_line = relied.underside_clock(
                        underside_profiles, relied.ASKED_SPAN)
                else:
                    underside_line = _pnote
                    underside_refusal = _pnote
            else:
                underside_line = _snote
                underside_refusal = _snote

        dial_applied = bool(gt_dial) and resp.get("gt_dial_applied") is True
        press_applied = bool(gt_press) and resp.get("gt_press_applied") is True
        if underside_line:
            print(underside_line, file=sys.stderr)
        print()
        if use_held_skin:
            print(HELD_SKIN_LOUD)
        if gt_dial and not dial_applied:
            print(DIAL_NO_APPLY)
        elif dial_applied:
            print(dial_loud(self.dial_alpha))
        if gt_press and not press_applied:
            print(PRESS_NO_APPLY)
        elif press_applied:
            print(press_loud(self.press_strength, self.press_span))
        if absent:
            shown = "(no answer)"
            print("[the model did not answer you. It may have repeated a "
                  "training line. Type /raw to see it.]")
        else:
            shown = answer
            print(answer)
            sys.stdout.flush()

        self.last_sequel = sequel
        file_tail = should_file_sequel(sequel, declared)
        if sequel and not absent and declared:
            print()
            print("── extra speech (not the answer) — /sequel ──")
            print(sequel)

        _stamp_stderr(
            fetched_from, held_n,
            dial=self.dial_alpha if dial_applied else "",
            press_s=self.press_strength if press_applied else "",
            press_sp=self.press_span if press_applied else "")
        print(score_clock(place_mode or "none", len(keep), held_n),
              file=sys.stderr)
        if sequel and not absent:
            if file_tail:
                print("EXTRA: declared — filed " + str(len(sequel))
                      + " chars; a look will speak", file=sys.stderr)
            else:
                print("EXTRA: no !path — not filed " + str(len(sequel))
                      + " chars", file=sys.stderr)
        else:
            print("EXTRA: none", file=sys.stderr)
        # DECLARED CALL-SITE (C-half, disclosure). What ended this completion,
        # read off the reply run.py already holds. No behaviour changes here:
        # the stop list stands, EOS is not lifted, nothing is banned. Two
        # silences that were indistinguishable are now told apart every turn.
        print(relied.stopped_clock(resp), file=sys.stderr)
        names = [n for n, _ in named]
        masses = _masses_in_order(resp, names)
        # A piece that was placed and came back with no reading is NAMED, not
        # dropped. The all-fail case was already named; the partial case was
        # not, and a vanished span reads as a span that was never placed.
        unread = relied.unaccounted_spans(resp, names)
        if payload and resp.get("gt_relied_saw_softmax") is False:
            print(relied.NO_HOOK, file=sys.stderr)
            masses = []
        elif masses or unread:
            print(relied.masses_clock(masses, unread), file=sys.stderr)
        else:
            print(pre_clock or _relied_line(placed=bool(named)),
                  file=sys.stderr)
        sys.stderr.flush()

        extra = []
        if self.pending_revises:
            extra.append(("ref", self.pending_revises[0]))
            self.pending_revises = None

        try:
            pressed_tag = ""
            if press_applied:
                pressed_tag = str(self.press_span) + "-" + str(self.press_strength)
            bid, gen = turn_record.record_turn(
                asked=user_q, answered=shown, kind=mouth,
                fetched=fetched_from, skin_on=self.skin_on,
                backend=model.backend() or "", raw=self.last_raw,
                extra_tags=extra if extra else None, declared_path=declared,
                fetched_text=fetched_text, hold_refs=hold_refs,
                relied=masses,
                dialed=self.dial_alpha if dial_applied else "",
                pressed=pressed_tag)
            self.last_turn_id = bid
            del gen
            # DECLARED CALL-SITE (C-half, storage). The curve is filed as its
            # own block, @ref: to the turn just written -- F3's sibling, not a
            # body section. No series means no sibling: absence is structural,
            # never a row of zeros. Nothing here derives; relied.py already did.
            try:
                turn_record.record_curve(
                    bid, underside_series, underside_profiles,
                    note=underside_refusal)
            except PileError as e:
                print(f"turn pile refused the curve block: {e}",
                      file=sys.stderr)
            if file_tail:
                turn_record.record_sequel(
                    sequel, ref_id=bid, declared_path=declared)
                look_speech, look_engine = summon_look(declared, sequel)
                print()
                print("── look (leftover speech — not a verdict) ──")
                print(look_speech)
                try:
                    turn_record.record_look(
                        look_speech, ref_id=bid, engine=look_engine,
                        declared_path=declared)
                except PileError as e:
                    print(f"turn pile refused the look block: {e}",
                          file=sys.stderr)
        except PileError as e:
            print(f"turn pile refused: {e}", file=sys.stderr)
            self.last_turn_id = ""
        return "loop"

    def step(self, msg):
        import io
        import contextlib
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = self.handle(msg)
        face = out.getvalue()
        clerk = err.getvalue()
        tab, tab_body = "", ""
        low = (msg or "").strip().lower()
        head = low.split()[0] if low else ""
        if head in _SUMMON_TABS:
            tab = head[1:]
            tab_body = face.strip() or clerk.strip()
        return Step(
            face=face, clerk=clerk,
            quit=(status == "quit"),
            tab=tab, tab_body=tab_body)

    def repl(self):
        rc = self.boot()
        if rc:
            return rc
        while True:
            try:
                msg = input(
                    "\nyou @ turn " + str(self.turn_n + 1) + " › ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if not msg:
                continue
            st = self.step(msg)
            if st.face:
                sys.stdout.write(st.face)
                if not st.face.endswith("\n"):
                    sys.stdout.write("\n")
                sys.stdout.flush()
            if st.clerk:
                sys.stderr.write(st.clerk)
                if not st.clerk.endswith("\n"):
                    sys.stderr.write("\n")
                sys.stderr.flush()
            if st.quit:
                return 0


def main():
    """TTY: the compose-and-edit shell. --repl: the old one-line input()."""
    argv = [a for a in sys.argv[1:] if a]
    if "--repl" in argv:
        return Talk().repl()
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            import talk_tui
            import textual  # noqa: F401 — talk_tui puts GT_WEB_SITE on sys.path
        except ImportError as e:
            print(
                "compose-and-edit shell could not load (" + str(e)
                + "). Falling back to the one-line input. "
                + "That line sends on Return and cannot walk wrapped words.",
                file=sys.stderr)
            return Talk().repl()
        return talk_tui.main(["--live"])
    return Talk().repl()


if __name__ == "__main__":
    sys.exit(main())
