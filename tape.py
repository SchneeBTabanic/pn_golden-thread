"""
tape.py — split one completion into face + sequel. No regex.

The first span is the answer he asked for. The rest is a found saying
(the virtual second model). Rules are line facts he can refuse:

  - a clerk label the model parroted (MOUTH: / FETCHED: / SKIN: / BACKEND:)
  - after some answer text, a new line that opens a quiz
"""

CLERK_LABELS = (
    "ASKED", "ANSWERED", "MOUTH", "FETCHED", "SKIN", "BACKEND",
    "STAMP", "SHAPE", "DECLARED", "SEQUEL", "WALK", "LOOK",
    "COMMENT", "ENGINE", "HELD", "RELEASED",
    "PROBE", "PREMISE", "RENDERED", "PLACED", "LAW",
    "ASK", "CLOSED", "REVISES", "RESET",
)

QUIZ_OPENERS = (
    "What ", "What's ", "Whats ", "Who ", "Who's ", "Whom ",
    "How ", "Where ", "When ", "Why ",
    "Do ", "Does ", "Did ", "Can ", "Could ",
    "Is ", "Are ", "Was ", "Were ",
)


def clerk_label(line):
    """HEAD of 'NAME:' or 'NAME: value' when NAME is ALLCAPS/_ . Else None."""
    s = (line or "").strip()
    if ":" not in s:
        return None
    head = s.split(":", 1)[0]
    if not head or " " in head:
        return None
    for ch in head:
        if not (ch.isupper() or ch == "_"):
            return None
    return head


def is_quiz_opener(line):
    s = (line or "").strip()
    if not s:
        return False
    for p in QUIZ_OPENERS:
        if s.startswith(p):
            return True
    return False


def is_training_loop_line(line):
    """A line that is a training-pair marker, not an answer to him."""
    s = (line or "").strip()
    if s.startswith("# Input:") or s.startswith("# Output:"):
        return True
    if s == "The quick brown fox jumps over the lazy dog":
        return True
    return False


def _utf8_line_starts(raw):
    """splitlines() rows and the UTF-8 byte offset of each in unstripped raw."""
    raw = raw or ""
    lines = raw.splitlines()
    starts = []
    pos = 0
    for k, ln in enumerate(lines):
        if k > 0:
            if pos < len(raw) and raw[pos] == "\r":
                pos += 1
                if pos < len(raw) and raw[pos] == "\n":
                    pos += 1
            elif pos < len(raw) and raw[pos] == "\n":
                pos += 1
        starts.append(len(raw[:pos].encode("utf-8")))
        pos += len(ln)
    return lines, starts, len(raw.encode("utf-8"))


def split_tape(raw, asked=""):
    """Return (face, sequel, cut_byte). Face keeps going until a cut.

    cut_byte is the UTF-8 offset into unstripped raw where sequel begins.
    After R4 the face is a prefix: raw_utf8[:cut_byte] is that span.
    asked is unused (R4 removed asked-echo). Kept so callers do not drift.
    """
    del asked
    raw = raw or ""
    lines, starts, nbytes = _utf8_line_starts(raw)
    face = []
    had_content = False
    cut = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s:
            had_content = True
        lab = clerk_label(s) if s else None
        if lab in ("MOUTH", "FETCHED", "SKIN", "BACKEND", "STAMP"):
            cut = i
            break
        if had_content and any(x.strip() for x in face) and is_quiz_opener(s):
            cut = i
            break
        if is_training_loop_line(s):
            if any(x.strip() and not is_training_loop_line(x) for x in face):
                cut = i
                break
            if not any(x.strip() for x in face):
                return "", "\n".join(lines).strip(), 0
            cut = i
            break
        face.append(ln)
    if cut is None:
        return "\n".join(lines).strip(), "", nbytes
    cut_byte = starts[cut] if cut < len(starts) else nbytes
    return (
        "\n".join(lines[:cut]).strip(),
        "\n".join(lines[cut:]).strip(),
        cut_byte,
    )


def _take_caret_token(s, needle):
    """Remove one ^ or ^^ at a token boundary. No value after the sigil."""
    start = 0
    n = len(needle)
    while True:
        j = s.find(needle, start)
        if j < 0:
            return False, s
        if j > 0 and s[j - 1] not in " \t\n":
            start = j + 1
            continue
        after = s[j + n:]
        if needle == "^" and after.startswith("^"):
            start = j + 1
            continue
        if after[:1] not in ("", " ", "\t", "\n"):
            start = j + 1
            continue
        before = s[:j].rstrip()
        rest = after.strip()
        glued = (before + " " + rest).strip() if before else rest
        return True, glued


def parse_score_place(msg):
    """^ fold or ^^ raw, token boundary. Returns (mode_or_none, message)."""
    s = msg or ""
    found, rest = _take_caret_token(s, "^^")
    if found:
        return "raw", rest
    found, rest = _take_caret_token(s, "^")
    if found:
        return "fold", rest
    return None, s


def _take_bang(text, needle):
    """Value after a sigil, and the text with that sigil-and-value removed."""
    s = text or ""
    start = 0
    while True:
        j = s.find(needle, start)
        if j < 0:
            return "", s
        if j == 0 or s[j - 1] in " \t\n":
            after = s[j + len(needle):]
            if after[:1] in ("", " ", "\t", "\n"):
                val = after.strip()
                # stop this bang's value at the next bang
                k = 0
                while k < len(val):
                    if val[k] == "!" and (k == 0 or val[k - 1] in " \t"):
                        val = val[:k].strip()
                        break
                    k += 1
                before = s[:j].rstrip()
                rest_after = after.strip()
                if val and rest_after.startswith(val):
                    rest_after = rest_after[len(val):].strip()
                glued = (before + " " + rest_after).strip()
                return val, glued
        start = j + 1


def parse_bang_path(msg):
    """!path <method> anywhere. Returns (declared, message_unchanged)."""
    declared, _ = _take_bang(msg, "!path")
    return declared, msg or ""


def parse_ask_line(msg):
    """!ask <question> as the whole line. None if not an ask."""
    s = (msg or "").strip()
    if len(s) < 4 or s[:4].lower() != "!ask":
        return None
    rest = s[4:]
    if rest[:1] not in ("", " ", "\t"):
        return None
    return rest.strip()


def parse_closed_line(msg):
    """!closed <ref-or-index>. None if not a close."""
    s = (msg or "").strip()
    if len(s) < 7 or s[:7].lower() != "!closed":
        return None
    rest = s[7:]
    if rest[:1] not in ("", " ", "\t"):
        return None
    return rest.strip()


_REVISES_KEYS = ("rejected", "expanded", "narrowed", "invariant")


def parse_revises_line(msg):
    """/revises <ref> [key:\"note\" ...]. None if not revises.

    Closed four keys, human-typed. Nothing is inferred.
    """
    s = (msg or "").strip()
    if len(s) < 8 or s[:8].lower() != "/revises":
        return None
    rest = s[8:]
    if rest[:1] not in ("", " ", "\t"):
        return None
    rest = rest.strip()
    if not rest:
        return "", {}, "need a turn ref or a seat number"
    tok = rest.split(None, 1)[0]
    notes_src = rest[len(tok):].strip()
    notes = {}
    while notes_src:
        if ":" not in notes_src:
            return tok, notes, "revises notes must be key:\"text\""
        key, after = notes_src.split(":", 1)
        key = key.strip()
        if key not in _REVISES_KEYS:
            return tok, notes, "revises key not in rejected|expanded|narrowed|invariant"
        after = after.lstrip()
        if not after.startswith('"'):
            return tok, notes, "revises note must be quoted"
        end = after.find('"', 1)
        if end < 0:
            return tok, notes, "revises note missing closing quote"
        notes[key] = after[1:end]
        notes_src = after[end + 1:].strip()
    return tok, notes, ""


def parse_hold_line(msg):
    """hold: testimony, optional !awaits / !dissolves. None if not a hold."""
    s = (msg or "").strip()
    if len(s) < 5 or s[:5].lower() != "hold:":
        return None
    rest = s[5:].lstrip()
    awaits, rest = _take_bang(rest, "!awaits")
    dissolves, rest = _take_bang(rest, "!dissolves")
    return rest.strip(), awaits, dissolves


def should_file_sequel(sequel, declared):
    """A tail enters the pile only when he declared he cares about leftover speech.

    No declaration = no use = not filed. That is an exclusion you can count.
    Python does not score whether the tail 'sits on' the declared words.
    A second span looks; that speech is not a switch.
    """
    if not (sequel or "").strip():
        return False
    return bool((declared or "").strip())
