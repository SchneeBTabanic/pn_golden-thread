"""
witness/arithmetic.py — THE DECIDABLE CLAIM CHECKER.

Reads the model's answer, finds claims a computer can DECIDE, decides them, and
reports the ones that are WRONG -- with the arithmetic that proves it. Not a
score. Not a similarity. A decision with a proof the reader can redo by hand.

WHY. On 2026-08-14 a governed session answered nine questions about the letter
'r'. It said U+0072 is 112 (it is 114). It said 01110010 is 6 bits (it is 8).
It said the field holds eight 1s (it holds four). It said 'r' is "two bytes:
0x72 0x72". It said 01110010 is 53. The governance layer reported Phi=0.0178,
every signal clean, on the turn that said "6 bits". Five false statements, all
mechanically checkable, none caught -- because every auditor there measured
STYLE (similarity, fatigue, entropy, register, provenance category) and none
measured TRUTH.

NO REGULAR EXPRESSIONS. This file does not import `re` and must never import
it. Everything is read through witness/scan.py, which walks characters and
asks what a token IS. The sovereign's standing aversion is recorded in memory
(feedback-structure-not-filters): "there can never be enough words... it is a
red flag to me", with a live case where a regex in proxy.py silently deleted
any number ending a sentence, for weeks. An earlier draft of this file used
patterns and argued a closed-formal-notation exception; that argument was
mine, it was overruled on 2026-08-14, and it is withdrawn. The rewrite is also
simply better: `[0-9A-Fa-f]{4,6}` is a guess at a shape with a bound someone
chose, and `every character after "U+" is a hex digit` is the definition.

WHAT IT IS NOT. Not a fact-checker, ever. It cannot know whether Paris is the
capital of France. It decides only what is true or false by computation from
the literals present. Its reach is small, exactly stated, and never overstated:
check() reports what it examined AND what it declined to examine, so "nothing
found" can never be read as "nothing wrong".

ABSOLUTE RULE: a check that cannot decide MUST decline. Never guess, never
approximate, never report a likelihood. A wrong accusation costs more than a
missed error, because the whole worth of this organ is that when it speaks it
is right. That rule has already caught this file twice -- see _names_encoding.
"""
import codecs
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional

from checks import scan

INTEGRITY = {
    "conserves": "the arithmetic that proves each verdict -- every finding "
                 "carries the computation, so the checker is auditable and "
                 "never asks to be trusted",
    "discards": "nothing silently -- claims it cannot decide are counted and "
                "named, so a clean report cannot be misread as a checked one",
    "proves_it_by": "tests/test_arithmetic.py, whose cases are the false "
                    "statements from the real 2026-08-14 session transcript",
    "surfaced_as": "CONTRADICTED / (silence is never clearance)",
}

CONFIRMED = "CONFIRMED"
CONTRADICTED = "CONTRADICTED"

# English numerals, needed to read "eight bits". A numeral system is finite and
# fixed -- it is not an enumeration of PHRASINGS, which is what the standing
# rule forbids: no new numeral for eight arrives next year. Kept as small as
# the domain requires.
_NUMERALS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
             "eleven": 11, "twelve": 12, "sixteen": 16, "thirty-two": 32,
             "sixty-four": 64}


@dataclass
class Verdict:
    status: str
    claim: str
    proof: str
    kind: str


@dataclass
class Report:
    contradicted: List[Verdict] = field(default_factory=list)
    confirmed: List[Verdict] = field(default_factory=list)
    undecided_sentences: int = 0
    checked_sentences: int = 0

    @property
    def total_sentences(self) -> int:
        return self.checked_sentences + self.undecided_sentences

    def render(self) -> str:
        """States its own reach ALWAYS — 'no errors found' and 'nothing here
        was checkable' are different facts and must never print alike."""
        lines = []
        if self.contradicted:
            lines.append(f"{len(self.contradicted)} statement(s) in this answer "
                         f"are FALSE by computation:")
            for v in self.contradicted:
                lines.append(f"  - {v.proof}")
                lines.append(f'      in: "{_short(v.claim, 100)}"')
        if self.confirmed:
            lines.append(f"{len(self.confirmed)} statement(s) checked and correct: "
                         + "; ".join(v.proof for v in self.confirmed[:4]))
        if self.total_sentences == 0:
            lines.append("Decidable-claim check: nothing in this answer carried "
                         "a number, code point or binary field, so this check "
                         "had nothing to examine — that is not the same as clean.")
        else:
            # Leads with what WAS done, then what was not. Same reason as the
            # echo line: a sentence whose first clause is a negation gets read
            # as a failure by a small model summarising it.
            verdict = ("PASSED" if not self.contradicted else "FOUND ERRORS")
            lines.append(f"Decidable-claim check: {verdict} — "
                         f"{self.checked_sentences} of {self.total_sentences} "
                         f"sentence(s) carried something decidable and were "
                         f"decided by computation. The other "
                         f"{self.undecided_sentences} carried nothing this "
                         f"organ can decide, so they were NOT checked — which "
                         f"is not the same as clean. Only arithmetic is checked "
                         f"here; nothing in this report speaks to whether the "
                         f"rest is true.")
        return "\n".join(lines)


def _short(s: str, n: int) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n - 1] + "…"


# ---------------------------------------------------------------------------
# Reading a sentence's claims — by walking its words, never by matching.
# ---------------------------------------------------------------------------

def _unit_claims(sentence: str, unit_singular: str) -> List[int]:
    """Every "<N> bits" / "<N> bytes" claim in the sentence.

    Walks the words. A unit word takes its count from the word before it, or
    from its own hyphenated prefix ("6-bit"). Nothing is matched; each token is
    asked what it is."""
    found = []
    toks = scan.words(sentence)
    for i, tok in enumerate(toks):
        low = tok.lower()
        # "6-bit" / "16-bit": the count is joined to the unit by a hyphen.
        if "-" in low:
            head, _, tail = low.rpartition("-")
            if tail == unit_singular or tail == unit_singular + "s":
                n = scan.integer(head) if head.isdigit() else _NUMERALS.get(head)
                if n is not None:
                    found.append(n)
                    continue
        if low != unit_singular and low != unit_singular + "s":
            continue
        if i == 0:
            continue
        prev = toks[i - 1].lower()
        n = scan.integer(prev)
        if n is None:
            n = _NUMERALS.get(prev)
        if n is not None:
            found.append(n)
    return found


def _digit_count_claim(sentence: str):
    """"there are 8 '1's" -> (8, '1'). Walks words; asks what each one is."""
    toks = scan.words(sentence)
    for i, tok in enumerate(toks):
        # Quotes are removed from ANYWHERE in the token, not just its edges:
        # the model writes "1's" for the plural of the digit 1, so the
        # apostrophe sits INSIDE and edge-stripping cannot reach it. Dropping a
        # fixed set of quote characters is a character filter, not a pattern.
        low = "".join(c for c in tok.lower() if c not in "'\"‘’“”")
        target = None
        if low in ("1s", "0s"):
            target = low[0]
        elif low in ("ones", "zeros", "zeroes"):
            target = "1" if low == "ones" else "0"
        if target is None or i == 0:
            continue
        prev = toks[i - 1].lower()
        n = scan.integer(prev)
        if n is None:
            n = _NUMERALS.get(prev)
        if n is not None:
            return n, target
    return None


def _names_encoding(sentence: str) -> Optional[str]:
    """The character encoding named in this sentence, if any — asked of
    Python's own codec registry, not of a list I maintain.

    TWO PURPOSES, and the second is a guard against this file's own worst
    failure mode. First, it says which encoding a byte claim is about. Second,
    when a sentence names an encoding it SUPPLIES ITS OWN SUBJECT, and a check
    that would have to reach backward for one must decline. That guard was
    added after a real false accusation: replaying the 2026-08-14 session, the
    width check read "a code point is typically encoded as a single 16-bit or
    32-bit value" and accused it of misstating the width of a binary field two
    sentences earlier. The 16 belongs to UTF-16. Declining costs nothing; a
    wrong accusation costs the organ its only asset."""
    for tok in scan.words(sentence):
        low = tok.lower().strip(".,")
        if not low.startswith(("utf", "ascii", "latin", "iso-", "cp")):
            continue
        try:
            codecs.lookup(low)
        except LookupError:
            continue
        return low
    return None


def _encoding_for(sentence: str):
    """(python codec, display name) for a byte-level claim. UTF-8 is the
    default only when no encoding is named — never a guess over one that is."""
    named = _names_encoding(sentence)
    if named is None:
        return "utf-8", "UTF-8"
    if named.startswith("utf") and "16" in named:
        return "utf-16-be", "UTF-16"
    if named.startswith("utf") and "32" in named:
        return "utf-32-be", "UTF-32"
    return named, named.upper()


def _hex_run(sentence: str) -> List[int]:
    """A run of two or more ADJACENT hex literals is a byte sequence
    ("0x00 0x72"); a lone one is a value ("the 0x72 value"). Told apart by
    adjacency in the token stream — the notation's own layout, nothing else."""
    best: List[int] = []
    run: List[int] = []
    for tok in scan.words(sentence):
        v = scan.hex_value(tok)
        if v is None:
            if len(run) > len(best):
                best = run
            run = []
        else:
            run.append(v)
    if len(run) > len(best):
        best = run
    return best if len(best) >= 2 else []


# ---------------------------------------------------------------------------
# Subject continuity. An answer is ONE unit of reference.
# "The Unicode for 'r' is U+0072. This is a 6-bit value." makes its false claim
# in a sentence naming neither the character nor the field. A sentence-local
# checker misses it — measured, not assumed: the first run of the tests missed
# four of five real errors for exactly this reason.
# ---------------------------------------------------------------------------
@dataclass
class _Subject:
    char: Optional[str] = None
    codepoint_hex: Optional[str] = None
    binary: Optional[str] = None

    def update(self, sentence: str) -> None:
        ch = scan.find_quoted_char(sentence)
        if ch is not None:
            self.char = ch
        for tok in scan.words(sentence):
            if self.codepoint_hex is None or True:
                cp = scan.codepoint_text(tok)
                if cp is not None:
                    self.codepoint_hex = cp
                    break
        for tok in scan.words(sentence):
            b = scan.binary_field(tok)
            if b is not None:
                self.binary = b
                break


def _local_binary(sentence: str) -> Optional[str]:
    for tok in scan.words(sentence):
        b = scan.binary_field(tok)
        if b is not None:
            return b
    return None


def _local_codepoints(sentence: str) -> List[str]:
    out = []
    for tok in scan.words(sentence):
        cp = scan.codepoint_text(tok)
        if cp is not None:
            out.append(cp)
    return out


def _local_integers(sentence: str) -> List[int]:
    out = []
    for tok in scan.words(sentence):
        n = scan.integer(tok)
        if n is not None:
            out.append(n)
    return out


def _carried(from_sentence: bool) -> str:
    return "" if from_sentence else " (the subject established earlier in this answer)"


# ---------------------------------------------------------------------------
# The checks. Each returns a Verdict, or None meaning "not my case" — which is
# never the same as "this sentence is fine".
# ---------------------------------------------------------------------------

def _check_char_codepoint(s, subj):
    ch = scan.find_quoted_char(s)
    cps = _local_codepoints(s)
    if ch is None or not cps:
        return None
    true_cp = ord(ch)
    claimed = int(cps[0], 16)
    if claimed == true_cp:
        return Verdict(CONFIRMED, s, f"'{ch}' is U+{true_cp:04X} — correct",
                       "code point")
    return Verdict(CONTRADICTED, s,
                   f"'{ch}' is U+{true_cp:04X}, not U+{cps[0]}", "code point")


def _check_value_fits_bits(s, subj):
    """"'r' is U+0072 ... a 6-bit value" -> 114 does not fit in 6 bits."""
    if _local_binary(s) or subj.binary:
        return None                       # a written field: the width check owns it
    cps = _local_codepoints(s) or ([subj.codepoint_hex] if subj.codepoint_hex else [])
    if cps and cps[0]:
        value, shown = int(cps[0], 16), f"U+{cps[0]}"
    else:
        ch = scan.find_quoted_char(s) or subj.char
        if ch is None:
            return None
        value, shown = ord(ch), f"'{ch}'"
    for c in _unit_claims(s, "bit"):
        if not 0 < c <= 64:
            continue
        if value <= (1 << c) - 1:
            return Verdict(CONFIRMED, s, f"{shown} = {value} fits in {c} bits",
                           "value width")
        return Verdict(CONTRADICTED, s,
                       f"{shown} is {value}, which needs at least "
                       f"{max(1, value.bit_length())} bits — {c} bits holds at "
                       f"most {(1 << c) - 1}", "value width")
    return None


def _check_codepoint_value(s, subj):
    """"U+0072 ... is 112" -> it is 114."""
    cps = _local_codepoints(s)
    if not cps:
        return None
    true_val = int(cps[0], 16)
    skip = set(_unit_claims(s, "bit")) | set(_unit_claims(s, "byte"))
    for d in _local_integers(s):
        if str(d) == cps[0] or str(d) == cps[0].lstrip("0") or d in skip:
            continue
        if d == true_val:
            return Verdict(CONFIRMED, s, f"U+{cps[0]} = {true_val} decimal",
                           "code-point value")
        if 0 < d < 0x110000 and abs(d - true_val) <= max(64, true_val // 2):
            return Verdict(CONTRADICTED, s,
                           f"U+{cps[0]} is {true_val} in decimal, not {d}",
                           "code-point value")
    return None


def _check_binary_width(s, subj):
    local = _local_binary(s)
    if local is None and _names_encoding(s):
        return None                       # the sentence supplies its own subject
    field_ = local or subj.binary
    if field_ is None:
        return None
    width = len(field_)
    for c in _unit_claims(s, "bit"):
        if c == width:
            return Verdict(CONFIRMED, s, f"{field_} is {width} bits", "binary width")
        return Verdict(CONTRADICTED, s,
                       f"{field_} is {width} bits wide, not {c} — count the "
                       f"digits: there are {width} of them" + _carried(bool(local)),
                       "binary width")
    return None


def _check_digit_count(s, subj):
    local = _local_binary(s)
    field_ = local or subj.binary
    if field_ is None:
        return None
    claim = _digit_count_claim(s)
    if claim is None:
        return None
    n_claimed, digit = claim
    actual = field_.count(digit)
    if actual == n_claimed:
        return Verdict(CONFIRMED, s, f"{field_} contains {actual} '{digit}'(s)",
                       "digit count")
    return Verdict(CONTRADICTED, s,
                   f"{field_} contains {actual} '{digit}'(s), not {n_claimed}"
                   + _carried(bool(local)), "digit count")


def _check_binary_value(s, subj):
    local = _local_binary(s)
    if local is None and _names_encoding(s):
        return None
    field_ = local or subj.binary
    if field_ is None:
        return None
    true_val = int(field_, 2)
    skip = set(_unit_claims(s, "bit")) | set(_unit_claims(s, "byte")) | {len(field_)}
    for d in _local_integers(s):
        if str(d) == field_ or d in skip:
            continue
        if d == true_val:
            return Verdict(CONFIRMED, s, f"binary {field_} = {true_val} decimal",
                           "binary value")
        if 0 < d and abs(d - true_val) <= max(64, true_val // 2):
            return Verdict(CONTRADICTED, s,
                           f"binary {field_} is {true_val} in decimal, not {d}"
                           + _carried(bool(local)), "binary value")
    return None


def _check_stated_bytes(s, subj):
    """"two bytes: 0x72 0x72" -> checks the BYTE VALUES, not just the count.

    A claim can name the right number of bytes and the wrong bytes: 'r' in
    UTF-16 IS two bytes, but they are 0x00 0x72. The count check clears that
    sentence; only comparing values catches it."""
    claimed = _hex_run(s)
    if not claimed:
        return None
    if _names_encoding(s) is None:
        return None                       # no encoding named: not decidable
    enc, label = _encoding_for(s)
    ch = scan.find_quoted_char(s) or subj.char
    if ch is None:
        cps = _local_codepoints(s) or ([subj.codepoint_hex] if subj.codepoint_hex else [])
        if cps and cps[0]:
            ch = chr(int(cps[0], 16))
        else:
            outside = [scan.hex_value(t) for t in scan.words(s)]
            outside = [v for v in outside if v is not None and v not in claimed]
            if not outside:
                # The value being encoded may itself be the first of the run.
                outside = claimed[:1]
            try:
                ch = chr(outside[0])
            except (ValueError, OverflowError):
                return None
    try:
        actual = list(ch.encode(enc))
    except Exception:
        return None
    if len(claimed) != len(actual):
        return None                       # the count check owns that disagreement
    fmt = lambda bs: " ".join("0x%02X" % b for b in bs)
    if claimed == actual:
        return Verdict(CONFIRMED, s, f"'{ch}' in {label} is {fmt(actual)}",
                       "byte values")
    return Verdict(CONTRADICTED, s,
                   f"'{ch}' in {label} is {fmt(actual)}, not {fmt(claimed)}",
                   "byte values")


def _check_byte_length(s, subj):
    ch = scan.find_quoted_char(s) or subj.char
    if ch is None:
        return None
    claims = _unit_claims(s, "byte")
    if not claims:
        return None
    enc, label = _encoding_for(s)
    try:
        n_bytes = len(ch.encode(enc))
    except Exception:
        return None
    for c in claims:
        if c == n_bytes:
            return Verdict(CONFIRMED, s, f"'{ch}' is {n_bytes} byte(s) in {label}",
                           "encoded length")
        try:
            name = unicodedata.name(ch)
        except ValueError:
            name = f"U+{ord(ch):04X}"
        return Verdict(CONTRADICTED, s,
                       f"'{ch}' ({name}) is {n_bytes} byte(s) in {label}, not "
                       f"{c} — encoded: "
                       + " ".join("0x%02X" % b for b in ch.encode(enc)),
                       "encoded length")
    return None


_CHECKS = (_check_char_codepoint, _check_value_fits_bits, _check_codepoint_value,
           _check_binary_width, _check_digit_count, _check_binary_value,
           _check_stated_bytes, _check_byte_length)


def check(answer: str) -> Report:
    """Decide what can be decided. Never guess."""
    report = Report()
    subj = _Subject()
    for sentence in scan.sentences(answer):
        verdicts = []
        for fn in _CHECKS:
            try:
                v = fn(sentence, subj)
            except Exception:
                v = None      # a broken check decides nothing; it never accuses
            if v is not None:
                verdicts.append(v)
        subj.update(sentence)     # AFTER: a sentence is not its own referent
        if not verdicts:
            report.undecided_sentences += 1
            continue
        report.checked_sentences += 1
        for v in verdicts:
            (report.contradicted if v.status == CONTRADICTED
             else report.confirmed).append(v)
    return report
