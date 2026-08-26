"""
turn_record.py — the conversation as a scribe pile.

Minutes stay syntax: ASKED / ANSWERED / FETCHED / #id / MOUTH as the
keystroke. Python does not choose tag values (辻4740#1192). @act/@path
and other meaning seats are written only when a semantic pass generated
them (extra_tags / walk accepted). The clerk does not map a sigil onto
put-a-question or not-yet-discerned.

The gForth writer owns the vocabulary as a wordlist. Python never
imports it. The sheet is still the program.
"""
import hashlib
import os

from pile_io import JOINER, PileError, capture_append, load_pile
from tape import clerk_label

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TURNS = os.path.join(HERE, "piles", "turns.pn")


def turns_path():
    return os.environ.get("GT_TURN_PILE", DEFAULT_TURNS)


MOUTHS = (
    "file", "shape", "bare", "forget", "refuse-file", "sequel", "walk",
    "comment", "look", "hold", "release", "probe",
    "fetch", "search", "html",
    "refuse-fetch", "refuse-search", "refuse-html",
    "sheet",
    "ask", "closed-ask", "revises", "reset",
)

HOLD_BANNER = (
    "[HELD — testimony placed by the human, in stasis. Not fact, not error.\n"
    "Do not adopt it. Do not argue it away. Answer from yourself.\n"
    "If your answer contradicts it, say so plainly and leave it held.\n"
    "It is released only by the human, never by an answer.]"
)

PREMISE_BANNER = (
    "[PLACED PREMISE — for this rendering, the following testimony is operative.\n"
    "What follows is not the model holding anything: it is the weights' rendering\n"
    "of the question under this premise, recorded as a measurement.]"
)


def known_mouth(kind):
    """Closed class of REPL sigils. Unknown kind is a refuse, not a guess."""
    if kind not in MOUTHS:
        raise PileError(
            f"unknown mouth {kind!r} — not inferred from prose, not assigned "
            f"by the model")
    return kind


def mouth_tags(kind):
    """Kept so old tests can refuse an unknown mouth. Does not write values."""
    known_mouth(kind)
    return ("", "")


def field(body, name):
    """Take the text under NAME: until the next ALLCAPS-name: line."""
    label = name + ":"
    lines = body.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln == label or ln.startswith(label + " "):
            start = i
            first = ln[len(label):].lstrip()
            break
    if start is None:
        return ""
    out = [first] if first else []
    for ln in lines[start + 1:]:
        lab = clerk_label(ln)
        if lab is not None and lab != name:
            break
        out.append(ln)
    return "\n".join(out).strip()


def tag_values(block, key):
    return [v for k, v in block.get("tags") or [] if k == key]


def tag_first(block, key, default=""):
    for k, v in block.get("tags") or []:
        if k == key:
            return v
    return block.get("tagmap", {}).get(key, default)


def _hyphen(s):
    out = []
    for ch in (s or ""):
        if ch == " " or ch == "/":
            out.append("-")
        else:
            out.append(ch)
    text = "".join(out)
    while "--" in text:
        text = text.replace("--", "-")
    return text.strip("-") or "unnamed"


def _sha8(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:8]


def _minutes(kind, origin, name, topic):
    """Index and write-provenance only. No meaning-seat values."""
    known_mouth(kind)
    return [
        ("topic", topic),
        ("name", name),
        ("origin", origin),
        ("source", "runtime"),
        ("captured", "golden-thread"),
    ]


def ensure_session():
    """First block in a new pile: the session's refusals, living in structure."""
    _, blocks = load_pile(turns_path())
    for b in blocks:
        if tag_first(b, "topic") == "session":
            return None, None
    body = (
        "SESSION CHARTER. Practices that must not live only in a head.\n"
        "The gForth writer is the critic at keep-time. Python is the reader.\n"
        "This runtime stamps facts it holds. Meaning seats stay empty.\n"
        "§6 is his comparison against the same model with no wrapper.\n"
        "Awaits: he compares against ungoverned. Dissolves: he rules closed."
    )
    # Header is one line and 512 bytes in keep. Extra sayings live in the body.
    tags = [
        ("act", "hold-the-session-refusals"),
        ("path", "away-from-a-third-source"),
        ("aspect", "manifesting"),
        ("topic", "session"),
        ("name", "session-charter"),
        ("origin", "ai"),
        ("source", "runtime"),
        ("captured", "golden-thread"),
        ("gates", "section-six-comparison"),
        ("defers", "sovereign"),
        ("refuses", "clause-injection"),
        ("refuses", "clause-selection"),
        ("refuses", "layer-2"),
        ("refuses", "registry-of-checks"),
        ("rejected", "proxy-as-the-face"),
        ("rejected", "cosine-clause-selection"),
        ("rejected", "applies-when"),
        ("kept", "foundation"),
    ]
    return capture_append(turns_path(), body, tags, source="runtime")


def record_turn(asked, answered, kind, fetched="", skin_on=False,
                backend="", raw="", extra_tags=None, declared_path="",
                fetched_text="", hold_refs=None, relied=None,
                dialed="", pressed=""):
    """One completed Executor turn. Returns (block_id, genesis)."""
    ensure_session()
    fetched_line = fetched if fetched else "(nothing)"
    declared = (
        f"\nDECLARED:\n!path {declared_path}\n" if declared_path else ""
    )
    body = (
        f"ASKED:\n{asked}\n\n"
        f"ANSWERED:\n{answered}\n\n"
        f"MOUTH: {kind}\n"
        f"FETCHED: {fetched_line}\n"
        f"SKIN: {'on' if skin_on else 'off'}\n"
        f"BACKEND: {backend or '(unasked)'}\n"
        f"STAMP: {'fetched' if fetched else 'nothing-fetched'}"
        f"{declared}"
    )
    tags = _minutes(kind, "human", "turn", "turn")
    tags.append(("part", "skinned" if skin_on else "unmasked"))
    if backend:
        tags.append(("captured", _hyphen(backend)))
    if fetched:
        tags.append(("watches", _hyphen(fetched)[:80]))
        if fetched_text:
            tags.append(("quoting", "sha256:" + _sha8(fetched_text)))
    if declared_path:
        tags.append(("watches", _hyphen(declared_path)[:80]))
    for pair in extra_tags or []:
        key, val = pair
        if not key or not val:
            continue
        if " " in str(key) or " " in str(val):
            raise PileError("extra tag contains a space: " + str(key) + ":" + str(val))
        if key in ("act", "path", "ref"):
            tags.append((key, val))
    for href in hold_refs or []:
        if href:
            tags.append(("ref", href))
    for name, frac in relied or []:
        val = str(name) + "-" + ("%.2f" % float(frac))
        if " " in val:
            raise PileError("relied tag value contains a space: " + val)
        tags.append(("relied", val))
    if dialed:
        if " " in str(dialed):
            raise PileError("dialed tag value contains a space: " + str(dialed))
        tags.append(("part", "dialed"))
        tags.append(("dialed", str(dialed)))
    if pressed:
        if " " in str(pressed):
            raise PileError("pressed tag value contains a space: " + str(pressed))
        tags.append(("part", "pressed"))
        tags.append(("pressed", str(pressed)))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_curve(turn_ref, series, profiles=None, note=""):
    """The curve that annotates one turn, as its OWN block. Sibling, not a body.

    No series, no sibling. A refused split still files its SERIES.
    Nothing is derived here; relied.py already computed for the clock.
    """
    import relied

    if not series or not (series.get("bytes") or []):
        return None, None

    sections = [relied.series_body(series)]
    if profiles:
        sections.append(relied.profiles_body(profiles))
    else:
        sections.append(note or relied.CURVE_NO_PROFILES)
    body = "\n\n".join(x for x in sections if x)

    tags = [
        ("topic", "curve"),
        ("name", "curve"),
        ("origin", "ai"),
        ("source", "runtime"),
        ("captured", "golden-thread"),
        ("part", "curve"),
    ]
    tags.append(("act", "hold-the-curve-that-annotates-a-turn"))
    tags.append(("path", "toward-a-reading-that-can-be-resplit"))
    if turn_ref:
        tags.append(("ref", str(turn_ref)))
    for seat, name, seat_bin in relied.curve_bins(profiles):
        val = seat + "-" + str(name) + "-" + seat_bin
        if " " in val:
            raise PileError("binned tag value contains a space: " + val)
        tags.append(("binned", val))
    if not profiles:
        tags.append(("refuses", "splitting-a-series-that-does-not-reconcile"))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_file_refused(path, reason):
    """A file: that did not place. Absence enacted, not silent."""
    return record_place_refused("refuse-file", "file:", path, reason)


def record_place_refused(kind, sigil, target, reason):
    """A placement sigil that did not place. Absence enacted, not silent."""
    ensure_session()
    known_mouth(kind)
    if kind == "refuse-file":
        answered = "(file refused — " + reason + ")"
    else:
        answered = "(" + kind + " — " + reason + ")"
    body = (
        f"ASKED:\n{sigil} {target}\n\n"
        f"ANSWERED:\n{answered}\n\n"
        f"MOUTH: {kind}\n"
        f"FETCHED: (nothing)\n"
        f"STAMP: placement-refused"
    )
    tags = _minutes(kind, "human", "turn", "turn")
    tags.append(("part", "unmasked"))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_sequel(speech, ref_id="", declared_path=""):
    """The tail of one completion. Not the face. Returns (block_id, genesis)."""
    ensure_session()
    body = f"SEQUEL:\n{speech}"
    if declared_path:
        body += f"\n\nDECLARED:\n!path {declared_path}"
    tags = _minutes("sequel", "ai", "sequel", "sequel")
    tags.append(("part", "sequel"))
    if ref_id:
        tags.append(("ref", _ref_tag(ref_id)))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_look(speech, ref_id="", engine="", declared_path=""):
    """Second span on leftover speech. Body only. Not a switch."""
    ensure_session()
    body = f"LOOK:\n{speech}"
    if declared_path:
        body += f"\n\nDECLARED:\n!path {declared_path}"
    if engine:
        body += f"\n\nENGINE: {engine}"
    tags = _minutes("look", "ai", "look", "look")
    tags.append(("part", "look"))
    if engine:
        tags.append(("captured", _hyphen(engine)))
    if ref_id:
        tags.append(("ref", _ref_tag(ref_id)))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_walk(speech, accepted, refused, ref_id=""):
    """The sheet-walk. Body is the raw walk; accepted tags live on this block."""
    ensure_session()
    body = f"WALK:\n{speech}"
    if refused:
        body += "\n\nREFUSED:\n" + "\n".join(refused)
    tags = _minutes("walk", "ai", "walk", "walk")
    tags.append(("part", "walk"))
    for pair in accepted:
        tags.append(pair)
    if ref_id:
        tags.append(("ref", _ref_tag(ref_id)))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_sheet(speech, accepted, refused, ref_id=""):
    """A judged sheet-reading. Accepted meaning seats live on this block.

    Clerk copies pairs the human /keep'd. It does not invent values.
    """
    ensure_session()
    body = f"SHEET:\n{speech}"
    if refused:
        body += "\n\nREFUSED:\n" + "\n".join(refused)
    tags = _minutes("sheet", "ai", "sheet", "sheet")
    tags.append(("part", "sheet"))
    for pair in accepted:
        tags.append(pair)
    if ref_id:
        tags.append(("ref", _ref_tag(ref_id)))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_shape(speech, ref_id="", story_path=""):
    """Shape-speech. Not an answer. Returns (block_id, genesis)."""
    ensure_session()
    body = f"SHAPE:\n{speech}"
    tags = _minutes("shape", "ai", "shape", "shape")
    tags.append(("part", "shape"))
    if story_path:
        tags.append(("quoting", "sha256:" + _sha8(story_path)))
        tags.append(("watches", _hyphen(story_path)[:80]))
    if ref_id:
        tags.append(("ref", _ref_tag(ref_id)))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_comment(speech, ref_id=""):
    """What the last record is for. Body only. No @act / @path."""
    ensure_session()
    body = f"COMMENT:\n{speech}"
    tags = _minutes("comment", "ai", "comment", "comment")
    tags.append(("part", "comment"))
    if ref_id:
        tags.append(("ref", _ref_tag(ref_id)))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_forget(dropped):
    ensure_session()
    known_mouth("forget")
    body = (
        f"ASKED:\n/forget\n\n"
        f"ANSWERED:\n(dropped {dropped} turn(s) from the model window; "
        f"the pile was not rewritten)\n\n"
        f"MOUTH: forget\n"
        f"FETCHED: (nothing)\n"
        f"STAMP: window-dropped pile-untouched"
    )
    tags = _minutes("forget", "human", "forget", "forget")
    return capture_append(turns_path(), body, tags, source="runtime")


def record_ask(question):
    """A burning question. Only he closes it. Not a hold. Not in the face."""
    ensure_session()
    known_mouth("ask")
    body = "ASK:\n" + (question or "")
    tags = [
        ("topic", "ask"),
        ("name", "ask"),
        ("origin", "human"),
        ("source", "runtime"),
        ("captured", "golden-thread"),
        ("aspect", "prospective"),
        ("part", "ask"),
        ("awaits", "his-hand-on-closed"),
    ]
    return capture_append(turns_path(), body, tags, source="runtime")


def record_ask_closed(ask_ref, reason=""):
    """Close an ask. The ask block is not edited."""
    ensure_session()
    known_mouth("closed-ask")
    body = "CLOSED:\n" + (reason or "closed by hand")
    tags = [
        ("topic", "closed-ask"),
        ("name", "closed-ask"),
        ("origin", "human"),
        ("source", "runtime"),
        ("captured", "golden-thread"),
        ("aspect", "manifested"),
        ("part", "ask"),
        ("ref", ask_ref),
        ("verified", _hyphen(reason or "closed-by-hand")[:80]),
    ]
    return capture_append(turns_path(), body, tags, source="runtime")


def record_revises_mark(target_ref, notes=None):
    """The edge itself, as a block. Next turn also carries @ref."""
    ensure_session()
    known_mouth("revises")
    lines = ["REVISES:\n" + (target_ref or "")]
    for k in ("rejected", "expanded", "narrowed", "invariant"):
        if notes and notes.get(k):
            lines.append(k.upper() + ":\n" + notes[k])
    body = "\n\n".join(lines)
    tags = [
        ("topic", "revises"),
        ("name", "revises"),
        ("origin", "human"),
        ("source", "runtime"),
        ("captured", "golden-thread"),
        ("part", "revises"),
        ("ref", target_ref),
    ]
    return capture_append(turns_path(), body, tags, source="runtime")


def record_reset(old_path, new_path, reason=""):
    """Mark a pile cut. Does not delete the old pile."""
    ensure_session()
    known_mouth("reset")
    body = (
        "RESET:\n" + (reason or "fresh pile")
        + "\n\nFROM:\n" + (old_path or "")
        + "\n\nTO:\n" + (new_path or "")
    )
    tags = [
        ("topic", "reset"),
        ("name", "reset"),
        ("origin", "human"),
        ("source", "runtime"),
        ("captured", "golden-thread"),
        ("part", "reset"),
    ]
    return capture_append(turns_path(), body, tags, source="runtime")


def active_asks():
    """Asks with no closed-ask whose ref formed-token matches. Arrival order."""
    genesis, blocks = load_pile(turns_path())
    closed = set()
    for b in blocks:
        if tag_first(b, "topic") == "closed-ask":
            for v in tag_values(b, "ref"):
                tok = ref_formed_token(v)
                if tok:
                    closed.add(tok)
    asks = []
    for b in blocks:
        if tag_first(b, "topic") != "ask":
            continue
        formed = _formed_of(b)
        if formed and formed not in closed:
            asks.append(b)
    return genesis, asks


def resolve_ask_ref(token):
    """Index in /open (1-based), or hold-style traveling name / offset."""
    genesis, asks = active_asks()
    s = (token or "").strip()
    if s.isdigit():
        i = int(s)
        if 1 <= i <= len(asks):
            return genesis, asks[i - 1], ""
        return genesis, None, "ask index missed"
    genesis2, blocks = load_pile(turns_path())
    del genesis2
    if s.startswith("#"):
        s = s[1:]
    want_formed = ref_formed_token(s) if "/" in s else ""
    want_off = None
    if "#" in s and s.split("#", 1)[1].split("/", 1)[0].isdigit():
        want_off = int(s.split("#", 1)[1].split("/", 1)[0])
    elif s.isdigit():
        want_off = int(s)
    by_off = None
    by_formed = None
    for b in blocks:
        if tag_first(b, "topic") != "ask":
            continue
        if want_off is not None and b.get("offset") == want_off:
            by_off = b
        if want_formed and _formed_of(b) == want_formed:
            by_formed = b
    if by_off is not None:
        return genesis, by_off, ""
    if by_formed is not None:
        return genesis, by_formed, ""
    return genesis, None, ""


def resolve_turn_seat(token):
    """1-based seat in the post-forget turn list, or a traveling name."""
    genesis, turns = gather_turns(0)
    s = (token or "").strip()
    if s.isdigit():
        i = int(s)
        if 1 <= i <= len(turns):
            return genesis, turns[i - 1], ""
        return genesis, None, "turn seat missed (1.." + str(len(turns)) + ")"
    want_formed = ref_formed_token(s) if "/" in s else ""
    want_off = None
    if s.startswith("#"):
        s = s[1:]
    if "#" in s and s.split("#", 1)[1].split("/", 1)[0].isdigit():
        want_off = int(s.split("#", 1)[1].split("/", 1)[0])
    for b in turns:
        if want_off is not None and b.get("offset") == want_off:
            return genesis, b, ""
        if want_formed and _formed_of(b) == want_formed:
            return genesis, b, ""
        if traveling_name(genesis, b) == (token or "").strip():
            return genesis, b, ""
    return genesis, None, ""


def revises_edges():
    """[(from_turn, to_ref), ...] from @ref on turns and revises blocks."""
    genesis, blocks = load_pile(turns_path())
    out = []
    for b in blocks:
        topic = tag_first(b, "topic")
        if topic not in ("turn", "revises"):
            continue
        for v in tag_values(b, "ref"):
            if v:
                out.append((b, v, genesis))
    return out


def inquire_moves(turn_block):
    """Python-verified edges only. No guessed similarity."""
    if not turn_block:
        return []
    genesis, blocks = load_pile(turns_path())
    here = traveling_name(genesis, turn_block)
    formed = _formed_of(turn_block)
    moves = []
    for v in tag_values(turn_block, "ref"):
        moves.append(("revises-out", v))
    for b in blocks:
        if not is_turn(b):
            continue
        src = traveling_name(genesis, b)
        if src == here:
            continue
        for v in tag_values(b, "ref"):
            tok = ref_formed_token(v)
            if formed and tok == formed:
                moves.append(("revises-in", src))
    seen = set()
    uniq = []
    for kind, ref in moves:
        key = kind + ":" + ref
        if key in seen:
            continue
        seen.add(key)
        uniq.append((kind, ref))
    return uniq


def fold_articulate(start, end):
    """Deterministic recap of seats start..end (1-based, post-forget). No model."""
    genesis, turns = gather_turns(0)
    n = len(turns)
    if start < 1 or end < start or end > n:
        return "", "fold range missed (1.." + str(n) + " after /forget)"
    span = turns[start - 1:end]
    span_formed = set(_formed_of(b) for b in span)
    _g, asks = active_asks()
    del _g
    lines = [
        "── fold (articulation — no model) ──",
        "seats " + str(start) + ".." + str(end) + " of " + str(n)
        + " after last /forget",
    ]
    alive = []
    for a in asks:
        tes = field(a["body"], "ASK")
        alive.append(traveling_name(genesis, a) + "  " + (tes or "").split("\n", 1)[0])
    lines.append("ALIVE (open !ask, whole pile, still burning):")
    if alive:
        for i, row in enumerate(alive, 1):
            lines.append("  " + str(i) + ". " + row)
    else:
        lines.append("  (none)")
    lines.append("REVISES (asserted edges touching this span):")
    any_edge = False
    for b, v, _g in revises_edges():
        src_form = _formed_of(b)
        dst_form = ref_formed_token(v)
        if src_form in span_formed or dst_form in span_formed:
            lines.append("  " + traveling_name(genesis, b) + " -> " + v)
            any_edge = True
    if not any_edge:
        lines.append("  (none)")
    lines.append("ISOLATED (turns in span with no @ref):")
    isolated = False
    for b in span:
        if tag_first(b, "topic") != "turn":
            continue
        if tag_values(b, "ref"):
            continue
        isolated = True
        asked = (field(b["body"], "ASKED") or "").split("\n", 1)[0]
        lines.append("  " + traveling_name(genesis, b) + "  " + asked)
    if not isolated:
        lines.append("  (none)")
    lines.append("ONE NEXT (oldest open ask, else quiet):")
    if asks:
        tes = field(asks[0]["body"], "ASK")
        lines.append("  " + (tes or "").strip())
    else:
        lines.append("  span is quiet — no open !ask")
    return "\n".join(lines), ""


def record_hold(testimony, awaits="", dissolves=""):
    """Testimony in stasis. No model call. Returns (three-part, genesis)."""
    ensure_session()
    known_mouth("hold")
    body = "HELD:\n" + (testimony or "")
    tags = [
        ("topic", "held"),
        ("name", "held"),
        ("origin", "human"),
        ("source", "runtime"),
        ("captured", "golden-thread"),
        ("aspect", "prospective"),
        ("part", "held"),
    ]
    if awaits:
        tags.append(("awaits", _hyphen(awaits)[:80]))
    if dissolves:
        tags.append(("dissolves", _hyphen(dissolves)[:80]))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_probe(asked, premise, rendered, stamp, turn_ref, hold_refs=None,
                 relied=None):
    """A measurement under a placed premise. Not an answer. Never edited in."""
    ensure_session()
    known_mouth("probe")
    body = (
        f"PROBE:\n{asked}\n\n"
        f"PREMISE:\n{premise}\n\n"
        f"RENDERED:\n{rendered}\n\n"
        f"STAMP: {stamp}"
    )
    tags = _minutes("probe", "ai", "probe", "probe")
    tags.append(("part", "probe"))
    tags.append(("touched", "probe"))
    if turn_ref:
        tags.append(("ref", _ref_tag(turn_ref)))
    for href in hold_refs or []:
        if href:
            tags.append(("ref", _ref_tag(href)))
    tags.append(("quoting", "sha256:" + _sha8(premise)))
    for name, frac in relied or []:
        val = str(name) + "-" + ("%.2f" % float(frac))
        if " " in val:
            raise PileError("relied tag value contains a space: " + val)
        tags.append(("relied", val))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_placed_file(path, content):
    """Mint the placed file as a block. Its traveling name is the span id."""
    ensure_session()
    body = "PLACED:\n" + (content or "")
    tags = [
        ("topic", "placed"),
        ("name", "placed"),
        ("origin", "human"),
        ("source", "runtime"),
        ("captured", "golden-thread"),
        ("part", "placed"),
    ]
    if path:
        tags.append(("watches", _hyphen(path)[:80]))
    if content:
        tags.append(("quoting", "sha256:" + _sha8(content)))
    return capture_append(turns_path(), body, tags, source="runtime")


def record_law_text(text):
    """Mint the placed law as a block. Its traveling name is the law span id."""
    ensure_session()
    body = "LAW:\n" + (text or "")
    tags = [
        ("topic", "law"),
        ("name", "law"),
        ("origin", "human"),
        ("source", "runtime"),
        ("captured", "golden-thread"),
        ("part", "law"),
        ("quoting", "sha256:" + _sha8(text or "")),
    ]
    return capture_append(turns_path(), body, tags, source="runtime")


def hold_testimony(block):
    return field((block or {}).get("body", ""), "HELD")


def build_premise_body(holds):
    """Testimonies only, pile order. The banner is prompt-only."""
    parts = []
    for h in holds or []:
        tes = hold_testimony(h)
        if tes:
            parts.append(tes)
    return "\n\n".join(parts)


def build_premise_prompt(holds):
    """Banner then testimonies. Not the HELD conversation banner."""
    body = build_premise_body(holds)
    if body:
        return PREMISE_BANNER + "\n" + body
    return PREMISE_BANNER


def verify_placed_pin(path, pin):
    """Re-read a placed file against the turn's quoting pin.

    Returns (FileRead, "") on match, (None, named reason) on refuse.
    """
    import file_read
    got = file_read.read_placed(path)
    if not got.ok:
        return None, "file refused — " + (got.refused or "unreadable")
    now = "sha256:" + _sha8(got.content)
    if not pin:
        return None, "quoting pin absent"
    if now != pin:
        return None, "file drifted — pin " + pin + " now " + now
    return got, ""


def holds_for_probe(ref_tok=""):
    """Active holds, or one named hold. Returns (genesis, holds, refuse)."""
    genesis, active = active_holds()
    want = (ref_tok or "").strip()
    if want:
        _, held, _note = resolve_hold_ref(want)
        if held is None:
            return genesis, [], "not an active hold."
        formed = _formed_of(held)
        for h in active:
            if _formed_of(h) == formed:
                return genesis, [h], ""
        return genesis, [], "not an active hold."
    if not active:
        return genesis, [], "nothing is held."
    return genesis, active, ""


def record_release(hold_ref, reason):
    """A release block. The held block is never edited."""
    ensure_session()
    known_mouth("release")
    body = "RELEASED:\n" + (reason or "")
    tags = [
        ("topic", "release"),
        ("name", "release"),
        ("origin", "human"),
        ("source", "runtime"),
        ("captured", "golden-thread"),
        ("part", "release"),
        ("ref", hold_ref),
        ("verified", _hyphen(reason)[:80]),
    ]
    return capture_append(turns_path(), body, tags, source="runtime")


def _formed_of(block):
    return block.get("formed") or tag_first(block, "formed")


def ref_formed_token(ref):
    s = str(ref or "")
    if "/" in s:
        return s.rsplit("/", 1)[-1]
    return ""


def active_holds():
    """Holds with no release whose ref formed-token matches. Arrival order."""
    genesis, blocks = load_pile(turns_path())
    released = set()
    for b in blocks:
        if tag_first(b, "topic") == "release":
            for v in tag_values(b, "ref"):
                tok = ref_formed_token(v)
                if tok:
                    released.add(tok)
    holds = []
    for b in blocks:
        if tag_first(b, "topic") != "held":
            continue
        formed = _formed_of(b)
        if formed and formed not in released:
            holds.append(b)
    return genesis, holds


def resolve_hold_ref(token):
    """Fast path: offset. Authoritative: formed token. Disclosed miss+match."""
    genesis, blocks = load_pile(turns_path())
    s = (token or "").strip()
    if s.startswith("#"):
        s = s[1:]
    want_formed = ref_formed_token(s) if "/" in s else ""
    want_off = None
    if "#" in s and s.split("#", 1)[1].split("/", 1)[0].isdigit():
        want_off = int(s.split("#", 1)[1].split("/", 1)[0])
    elif s.isdigit():
        want_off = int(s)
    by_off = None
    by_formed = None
    for b in blocks:
        if tag_first(b, "topic") != "held":
            continue
        if want_off is not None and b.get("offset") == want_off:
            by_off = b
        if want_formed and _formed_of(b) == want_formed:
            by_formed = b
    if by_off is not None:
        return genesis, by_off, ""
    if by_formed is not None:
        note = (
            "offset missed; formed-token matched "
            + traveling_name(genesis, by_formed)
        )
        return genesis, by_formed, note
    return genesis, None, ""


def _ref_tag(ref_id):
    """A ref: value is already three-part, or we refuse to invent formed."""
    s = str(ref_id or "")
    if s.startswith("辻") and "#" in s and "/" in s:
        return s
    if s.startswith("#") and "/" in s:
        genesis, _ = load_pile(turns_path())
        return (genesis + s) if genesis else s
    raise PileError(
        f"ref {s!r} is not three-part 辻genesis#offset/formed. "
        f"The runtime does not invent a formed token.")


def traveling_name(genesis, block):
    if isinstance(block, dict):
        off = block.get("offset", block.get("id"))
        formed = block.get("formed") or tag_first(block, "formed")
        if genesis and off is not None and formed:
            return f"{genesis}#{off}/{formed}"
        if off is not None:
            return f"#{off}"
        return "(no traveling name — this pile is not linkable)"
    s = str(block or "")
    if s.startswith("辻") and "/" in s:
        return s
    if genesis and s:
        return f"{genesis}#{s}" if "#" not in s else s
    if s:
        return f"#{s}"
    return "(no traveling name — this pile is not linkable)"


def is_turn(block):
    """A turn, and not something that merely annotates one.

    Append-only: a curve mistagged topic:turn stays on disk. The reader
    excludes part:curve so /history does not render it as a blank turn.
    """
    if tag_first(block, "topic") != "turn":
        return False
    return tag_first(block, "part") != "curve"


def gather_turns(limit):
    """Last `limit` topic:turn blocks after the latest /forget. A VIEW."""
    genesis, blocks = load_pile(turns_path())
    cut = -1
    for i, b in enumerate(blocks):
        if tag_first(b, "topic") == "forget":
            cut = i
    turns = [b for i, b in enumerate(blocks)
             if is_turn(b) and i > cut]
    keep = turns[-limit:] if limit else turns
    return genesis, keep


def gather_turns_before(probed, limit):
    """History strictly before `probed` in pile order, after the last
    /forget that itself sits before it. Later turns are not in the window."""
    genesis, blocks = load_pile(turns_path())
    probed_off = None
    if isinstance(probed, dict):
        probed_off = probed.get("offset")
    probed_i = len(blocks)
    cut = -1
    for i, b in enumerate(blocks):
        if probed_off is not None and b.get("offset") == probed_off:
            probed_i = i
        if tag_first(b, "topic") == "forget" and i < probed_i:
            cut = i
    # offset miss: still cut forgets that appear before the end
    if probed_i == len(blocks) and probed_off is not None:
        for i, b in enumerate(blocks):
            if tag_first(b, "topic") == "forget":
                if b.get("offset", 0) < probed_off:
                    cut = i
    turns = [b for i, b in enumerate(blocks)
             if is_turn(b) and i > cut and i < probed_i]
    keep = turns[-limit:] if limit else turns
    return genesis, keep


def view_for_model(limit, selector=""):
    """Text handed to the Executor. Declares itself a derived view."""
    genesis, keep = gather_turns(limit)
    if selector and ":" in selector:
        key, val = selector.split(":", 1)
        keep = [b for b in keep if val in tag_values(b, key)]
    if not keep:
        return ""
    parts = [
        "[DERIVED VIEW of the turn pile — last "
        f"{len(keep)} turn(s). This is not the pile. "
        "Seat numbers in this window will not survive another gather. "
        "Traveling names are 辻genesis#offset/formed when the pile is linkable.]",
    ]
    if not genesis:
        parts.append(
            "[This turn pile has no usable @genesis:. Nothing here invents "
            "a substitute. Relations in this window are seat numbers only.]")
    genesis2, all_turns = gather_turns(0)
    del genesis2
    extra = len(all_turns) - len(keep)
    dropped_note = ""
    if extra > 0:
        dropped_note = f"[{extra} earlier turn(s) not included in this view]"
    for b in keep:
        name = traveling_name(genesis, b)
        asked = field(b["body"], "ASKED")
        answered = field(b["body"], "ANSWERED")
        parts.append(
            f"Turn {name} — asked: {asked}\nTurn {name} — answered: {answered}")
    if dropped_note:
        parts.append(dropped_note)
    return JOINER.join(parts)


def last_turn():
    """Last Executor turn in the pile, including those before a /forget."""
    genesis, blocks = load_pile(turns_path())
    turns = [b for b in blocks if is_turn(b)]
    if not turns:
        return genesis, None
    return genesis, turns[-1]
