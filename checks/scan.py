"""
witness/scan.py — reading text WITHOUT pattern matching.

NO REGULAR EXPRESSIONS. NO `re` IMPORT. Not in this file and not in anything
that uses it. This is a standing prohibition from the sovereign (2026-08-14),
and it is stricter than the older "structure, not filters" rule: that rule
allowed an exception for closed formal notations, and this supersedes it. The
exception was my argument, not his, and it is withdrawn.

WHY IT IS ALSO BETTER, not merely obeyed. A pattern like `[0-9A-Fa-f]{4,6}` is
a GUESS AT THE SHAPE of a hex literal -- it says "four to six of these
characters", which is a bound someone chose and which will one day be wrong.
Reading the token instead:

    tok.startswith("U+") and every character after it is a hex digit

is the DEFINITION of the notation. It cannot be too narrow, cannot be too
wide, has no bound to tune, and cannot rot -- there is no list to extend when
a case is missed, because there is no list. Where the regex version needed a
comment explaining why the bounds were chosen, this version needs none: it
says what a code point IS.

The three things this module provides, all by plain scanning:

  sentences(text)   -> split on terminal punctuation, walking characters
  words(text)       -> tokens with surrounding punctuation stripped
  reading a token   -> binary_field / codepoint / hex_value / integer /
                       quoted_char / unit_word, each answering None when the
                       token is not that thing

ONE SCANNER, NOT TWO. Both witness organs read text through this file, so a
change to what counts as a token changes both together. Two hand-maintained
readers of one notation drift -- this project has been bitten by exactly that.
"""

INTEGRITY = {
    "conserves": "the token exactly as written, so every finding can quote the "
                 "text it read rather than a normalised version of it",
    "discards": "nothing by pattern -- a token this module cannot read is "
                "returned as unread, never silently skipped",
    "proves_it_by": "tests/test_scan.py",
    "surfaced_as": "None from every reader that does not recognise its input",
}

_HEX_DIGITS = "0123456789abcdefABCDEF"
_DIGITS = "0123456789"
_TERMINALS = ".!?"
# Punctuation that can sit around a word without being part of it. A fixed
# inventory of ASCII/Unicode punctuation, not a vocabulary of words -- nothing
# here ever needs a new entry because someone phrased something differently.
_EDGE = " \t\r\n,;:()[]{}\"'`“”‘’—–…"
_QUOTES = "'\"‘’“”"


def sentences(text):
    """Split into sentences by walking characters.

    Terminal punctuation is `.!?` followed by whitespace or end of line. A
    colon is NOT terminal: it introduces. Measured, not assumed -- treating
    ':' as a terminator severed "represented as two bytes: 0x72 0x72" between
    the encoding and its byte list, and the claim then could not be decided at
    all.

    A line break also ends a sentence, because a model writing a list puts one
    claim per line without punctuating it."""
    out = []
    for line in (text or "").splitlines():
        buf = []
        i = 0
        n = len(line)
        while i < n:
            ch = line[i]
            buf.append(ch)
            if ch in _TERMINALS:
                # A '.' inside a number ("24.2") or an abbreviation is not
                # terminal: it must be followed by a space or the line's end.
                nxt = line[i + 1] if i + 1 < n else " "
                if nxt.isspace():
                    s = "".join(buf).strip()
                    if s:
                        out.append(s)
                    buf = []
            i += 1
        s = "".join(buf).strip()
        if s:
            out.append(s)
    return out


def words(text):
    """Tokens, split on whitespace, with edge punctuation removed.

    SENTENCE PUNCTUATION IS STRIPPED FROM THE END ONLY, never the start. A
    leading '.' is part of the number in ".5", and stripping both ends would
    silently turn ".5" into "5" — a MISREAD, which is the one outcome this
    whole module exists to avoid. Stripped from the right, ".5" survives as
    ".5", which decimal_number() then declines to read at all: it wants digits
    before the separator. Declining is safe; misreading is not.

    Found by a test, not by inspection: leaving '.' out of the edge set
    entirely left "bits." unrecognised as a unit word, and four real errors
    went uncaught in the rewrite."""
    out = []
    for raw in (text or "").split():
        tok = raw.strip(_EDGE).rstrip(_TERMINALS).strip(_EDGE)
        if tok:
            out.append(tok)
    return out


def raw_words(text):
    """Tokens with their punctuation still attached, in order. Needed where the
    surrounding quotes are the information — a quoted single character."""
    return list((text or "").split())


# ---------------------------------------------------------------------------
# Readers. Each answers None when the token is not the thing it reads.
# None means "not this", never "malformed" and never "probably".
# ---------------------------------------------------------------------------

def binary_field(tok):
    """A written binary field: four or more characters, every one 0 or 1.

    Below four characters the notation is genuinely ambiguous with an ordinary
    number ("10" is far more often ten than two), so it is not read. That is a
    statement about what is decidable, not a tuned threshold."""
    if len(tok) < 4:
        return None
    for ch in tok:
        if ch != "0" and ch != "1":
            return None
    return tok


def codepoint(tok):
    """`U+0072` -> 114. The definition: 'U+' then hex digits, nothing else."""
    if len(tok) < 3:
        return None
    if tok[0] not in "Uu" or tok[1] != "+":
        return None
    body = tok[2:]
    if not body:
        return None
    for ch in body:
        if ch not in _HEX_DIGITS:
            return None
    return int(body, 16)


def codepoint_text(tok):
    """The hex digits of a code point token, as written (for quoting back)."""
    if codepoint(tok) is None:
        return None
    return tok[2:]


def hex_value(tok):
    """`0x72` -> 114. The definition: '0x' then hex digits, nothing else."""
    if len(tok) < 3:
        return None
    if tok[0] != "0" or tok[1] not in "xX":
        return None
    body = tok[2:]
    if not body:
        return None
    for ch in body:
        if ch not in _HEX_DIGITS:
            return None
    return int(body, 16)


def integer(tok):
    """A plain decimal integer. Every character a digit, or nothing."""
    if not tok:
        return None
    for ch in tok:
        if ch not in _DIGITS:
            return None
    return int(tok)


def decimal_number(tok):
    """A decimal number, possibly fractional: 24.2, 512, 0.45.

    Read by walking: digits, at most one separator, digits. No pattern."""
    if not tok:
        return None
    seen_sep = False
    digits_before = digits_after = 0
    for ch in tok:
        if ch in _DIGITS:
            if seen_sep:
                digits_after += 1
            else:
                digits_before += 1
        elif ch in ".," and not seen_sep and digits_before:
            seen_sep = True
        else:
            return None
    if not digits_before:
        return None
    if seen_sep and not digits_after:
        return None
    return float(tok.replace(",", "."))


def quoted_char(raw_tok):
    """A single character in quotes: 'r', "r". Takes a RAW token (quotes intact).

    The definition: a quote, one character, a quote — possibly with trailing
    sentence punctuation outside."""
    tok = raw_tok.strip(" \t,;:()[]{}.!?")
    if len(tok) < 3:
        return None
    if tok[0] not in _QUOTES or tok[-1] not in _QUOTES:
        return None
    inner = tok[1:-1]
    if len(inner) != 1:
        return None
    return inner


def find_quoted_char(text):
    """The first single-quoted character in the text, or None."""
    for raw in raw_words(text):
        ch = quoted_char(raw)
        if ch is not None:
            return ch
    return None
