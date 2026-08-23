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


def is_divider(line):
    """Clerk slab in ── ──. Same family as extra speech / prior record."""
    s = (line or "").strip()
    if len(s) < 4:
        return False
    return s.startswith("──") and s.endswith("──")


def is_clerk_chrome(line):
    """A line that is minutes, not speech: empty, a divider, or NAME:."""
    s = (line or "").strip()
    if not s:
        return True
    if is_divider(s):
        return True
    return clerk_label(s) is not None


def is_echo_of_asked(line, asked):
    """This line is the question coming back, not a new quiz."""
    s = (line or "").strip()
    a = (asked or "").strip()
    if not s or not a:
        return False
    if s == a:
        return True
    return s in a


def _peel_chrome(lines, asked=""):
    """Drop leading clerk wrap and a parroted question. Speech starts after."""
    i = 0
    n = len(lines)
    while i < n:
        if is_clerk_chrome(lines[i]) or is_echo_of_asked(lines[i], asked):
            i += 1
            continue
        break
    return lines[i:]


def split_tape(raw, asked=""):
    """Return (face, sequel). Either may be empty. Face keeps going until a cut.

    A quiz opener cuts only after real speech is already in the face, and
    not when the line is the question he just typed (the wrap echoing ASKED).
    """
    lines = (raw or "").splitlines()
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
            if is_echo_of_asked(s, asked):
                face.append(ln)
                continue
            if not any(not is_clerk_chrome(x) for x in face):
                face.append(ln)
                continue
            cut = i
            break
        if is_training_loop_line(s):
            # The fox / # Input loop is not a sequel worth keeping as speech.
            # Cut here; caller treats an empty-or-junk face as no answer.
            if any(x.strip() and not is_training_loop_line(x) for x in face):
                cut = i
                break
            if not any(x.strip() for x in face):
                # started with the loop — no face at all
                return "", "\n".join(lines).strip()
            cut = i
            break
        face.append(ln)
    if cut is None:
        kept = _peel_chrome(lines, asked)
        return "\n".join(kept).strip(), ""
    kept = _peel_chrome(lines[:cut], asked)
    return "\n".join(kept).strip(), "\n".join(lines[cut:]).strip()


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
