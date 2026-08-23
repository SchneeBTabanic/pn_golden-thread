"""
witness/quantities.py — TWO DIFFERENT NUMBERS FOR THE SAME KIND OF THING.

The third organ, and the one that answers a challenge this rebuild failed.

WHERE IT CAME FROM. A session ledger in the predecessor tree
(`/mnt/data/Codeberg/pn_vessel_llamacpp_c/vessel_data/ledgers/granite-3.3-8b/
20260320_164610.json`, 2026-03-20, granite-3.3-8b) records this:

  turn 1  "Voyager 1 is approximately 24.2 billion kilometers away"   -> "Clear."
  turn 2  "at an approximate distance from Earth of 24.2 billion km"  -> "Clear."
  turn 3  the human asks: "Compare your first claims against your second.
          What is the difference in distance between the two?"
          the model answers that the fetched content "pertains to routing
          algorithms used in data packet transmission"                -> "Clear."
  turn 4  "Voyager 1 was approximately 14.2 billion miles from Earth"  -> "Clear."

14.2 billion miles is 22.85 billion kilometres. The session states two
different distances for the same spacecraft and its own audit said "Clear."
four times. `witness/arithmetic.py` decided NOTHING on any of those turns --
measured, not assumed -- because nothing in them is a code point or a binary
field. That is the gap this file closes.

WHAT IT DOES. It extracts (number, unit) pairs from a session's answers,
normalises each into its physical dimension, and reports when the SAME
DIMENSION has been given TWO MATERIALLY DIFFERENT VALUES across the session.

WHAT IT REFUSES TO DO, and this is the whole design. It does NOT say either
value is wrong, because it cannot know the two refer to the same thing --
"24.2 billion km" and "22.85 billion km" might be two different spacecraft, or
the same one at two times. Deciding they are the same quantity would be
INFERRING A COREFERENCE, and inferring the human's or the model's meaning is
exactly what this project refuses (may record, never infer). So the organ
DISCLOSES A DIFFERENCE and hands the judgement to the reader:

    "Turn 1 said 24.2 billion kilometres. Turn 4 said 14.2 billion miles
     (= 22.85 billion kilometres). Those are different distances. If they were
     meant to be the same, one is wrong; that is yours to decide."

That is may-disclose-never-act with the reaching left in the human. An organ
that announced "turn 4 is FALSE" would be guessing, and a wrong accusation
costs more than a missed one.

NO REGULAR EXPRESSIONS. This file does not import `re`. Every quantity is read
by walking tokens through witness/scan.py and asking what each one is.

ON THE UNIT TABLE, honestly. It IS a list, and a list is the shape the
sovereign's standing rule is wary of. Two things make this one different in
kind from the filters that rule forbids, and they are stated here rather than
assumed. First, it is a table of MEASUREMENT CONVERSION FACTORS -- the thing a
unit table is for -- not an enumeration of ways a human might phrase something;
its entries are ratios fixed by the SI, and a missing entry causes a quantity
to go UNREAD and COUNTED, never misread. Second, it fails safe: an unknown unit
produces silence plus a reported count, where a filter's miss produces a wrong
answer silently. If even that is too close to the line, this organ should be
removed rather than argued for -- that ruling is the sovereign's, and an
earlier exception argued in this codebase was mine and was rightly overruled.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from checks import scan

INTEGRITY = {
    "conserves": "both stated values, in the units they were stated in, plus "
                 "the conversion -- the reader can always see the original "
                 "numbers and redo the arithmetic",
    "discards": "any judgement about WHICH value is right, and any inference "
                "that two quantities refer to the same thing -- both are the "
                "reader's, and the report says so in words",
    "proves_it_by": "tests/test_quantities.py, whose case is the real Voyager "
                    "ledger of 2026-03-20 that four 'Clear.' verdicts passed",
    "surfaced_as": "two different values for the same dimension, named",
}

# (dimension, factor to the canonical unit). CLOSED: fixed by standard.
_UNITS: Dict[str, Tuple[str, float]] = {
    # length -> metres
    "mm": ("length", 1e-3), "millimetre": ("length", 1e-3), "millimeter": ("length", 1e-3),
    "cm": ("length", 1e-2), "centimetre": ("length", 1e-2), "centimeter": ("length", 1e-2),
    "m": ("length", 1.0), "metre": ("length", 1.0), "meter": ("length", 1.0),
    "km": ("length", 1e3), "kilometre": ("length", 1e3), "kilometer": ("length", 1e3),
    "mi": ("length", 1609.344), "mile": ("length", 1609.344),
    "ft": ("length", 0.3048), "foot": ("length", 0.3048), "feet": ("length", 0.3048),
    "in": ("length", 0.0254), "inch": ("length", 0.0254),
    "au": ("length", 1.495978707e11),
    "ly": ("length", 9.4607304725808e15), "light-year": ("length", 9.4607304725808e15),
    # mass -> kilograms
    "mg": ("mass", 1e-6), "g": ("mass", 1e-3), "gram": ("mass", 1e-3),
    "kg": ("mass", 1.0), "kilogram": ("mass", 1.0),
    "tonne": ("mass", 1e3),
    # "pound"/"lb" are deliberately absent. "84 pounds" is money at least as
    # often as mass; this organ cannot tell which without reading the sentence.
    # time -> seconds
    "ms": ("time", 1e-3), "s": ("time", 1.0), "second": ("time", 1.0),
    "min": ("time", 60.0), "minute": ("time", 60.0),
    "h": ("time", 3600.0), "hr": ("time", 3600.0), "hour": ("time", 3600.0),
    "day": ("time", 86400.0), "year": ("time", 31557600.0),
    # data -> bytes
    "byte": ("data", 1.0), "kb": ("data", 1e3), "mb": ("data", 1e6),
    "gb": ("data", 1e9), "tb": ("data", 1e12),
    # temperature and speed are deliberately ABSENT: temperature needs an
    # offset not a factor, and speed units are compound. Neither is decidable
    # by this table, so neither is attempted.
}

_CANONICAL = {"length": "metres", "mass": "kilograms", "time": "seconds",
              "data": "bytes"}

_SCALES = {"thousand": 1e3, "million": 1e6, "billion": 1e9,
           "trillion": 1e12, "hundred": 1e2}

# How far apart two values must be before the difference is worth a word. Below
# this they are the same number stated with different rounding ("24.2" vs
# "24.19 billion km"), and reporting that would be noise -- the disclosure rule
# this project already learned: a report that fires on everything trains you to
# stop reading it.
_RELATIVE_TOLERANCE = 0.02


@dataclass
class Quantity:
    turn: int
    raw_text: str          # "24.2 billion kilometers"
    value: float           # in the canonical unit
    dimension: str
    unit_as_written: str


@dataclass
class QuantityReport:
    divergences: List[tuple] = field(default_factory=list)   # (dim, Quantity, Quantity)
    extracted: List[Quantity] = field(default_factory=list)
    unrecognised_units: int = 0

    def render(self) -> str:
        lines = []
        for dim, a, b in self.divergences:
            canon = _CANONICAL[dim]
            lines.append(
                f"TWO DIFFERENT {dim.upper()}S HAVE BEEN STATED in this session:")
            lines.append(f"    turn {a.turn}: {a.raw_text}  "
                         f"(= {_fmt(a.value)} {canon})")
            lines.append(f"    turn {b.turn}: {b.raw_text}  "
                         f"(= {_fmt(b.value)} {canon})")
            lines.append(f"    They differ by {_pct(a.value, b.value)}. This "
                         f"organ does NOT claim they refer to the same thing — "
                         f"if they were meant to, one of them is wrong, and "
                         f"which one is yours to decide.")
        # reach, always
        if not self.extracted:
            lines.append("Quantity check: no number-with-unit was found in this "
                         "session, so there was nothing to compare. That is not "
                         "the same as consistent.")
        else:
            dims = sorted({q.dimension for q in self.extracted})
            lines.append(
                f"Quantity check: {len(self.extracted)} quantit(y/ies) across "
                f"{len(dims)} dimension(s) ({', '.join(dims)}) were extracted and "
                f"compared; {self.unrecognised_units} number(s) carried a unit "
                f"this organ does not know and were NOT compared. Only numbers "
                f"with recognised units are checked — nothing here speaks to the "
                f"rest of the text.")
        return "\n".join(lines)


def _fmt(v: float) -> str:
    """Plain scientific form. An earlier version divided by 1e9 and then also
    appended "e9", printing "2.42e+04e9" — a number the reader cannot check by
    hand, which defeats the point of showing the conversion at all."""
    return f"{v:.6g}"


def _pct(a: float, b: float) -> str:
    hi, lo = max(a, b), min(a, b)
    if lo == 0:
        return "an unbounded amount"
    return f"{(hi - lo) / lo * 100:.1f}%"


def _extract(turn: int, text: str, report: QuantityReport) -> None:
    """Walk the words. A quantity is a number, optionally a scale word, then a
    unit — read by asking each token what it is, never by matching a pattern.

    NO REGULAR EXPRESSIONS anywhere in this file (see witness/scan.py for the
    standing prohibition and why the token walk is also the better reading)."""
    toks = scan.words(text)
    i = 0
    while i < len(toks):
        value = scan.decimal_number(toks[i])
        if value is None:
            i += 1
            continue
        parts = [toks[i]]
        j = i + 1
        if j < len(toks) and toks[j].lower() in _SCALES:
            value *= _SCALES[toks[j].lower()]
            parts.append(toks[j])
            j += 1
        if j >= len(toks):
            break
        unit_tok = toks[j]
        key = unit_tok.lower().rstrip(".").rstrip("s")
        if key not in _UNITS:
            # A number followed by a SCALE WORD and then a non-unit is a
            # magnitude whose unit this organ does not know. Counted and named,
            # never silently dropped. A bare number with no scale word is just a
            # number and is not a skipped quantity.
            if len(parts) > 1:
                report.unrecognised_units += 1
            i = j
            continue
        parts.append(unit_tok)
        dim, factor = _UNITS[key]
        report.extracted.append(
            Quantity(turn=turn, raw_text=" ".join(parts),
                     value=value * factor, dimension=dim,
                     unit_as_written=unit_tok))
        i = j + 1


def check(answers_by_turn: List[Tuple[int, str]]) -> QuantityReport:
    """`answers_by_turn` is [(turn_number, answer_text), ...] for the session.

    Reports each dimension for which two materially different values were
    stated. Compares the EXTREMES of each dimension, not every pair: if the
    largest and smallest agree within tolerance, nothing between them can
    diverge, and reporting every pair would bury the finding in arithmetic the
    reader did not ask for."""
    report = QuantityReport()
    for turn, text in answers_by_turn:
        _extract(turn, text, report)

    by_dim: Dict[str, List[Quantity]] = {}
    for q in report.extracted:
        by_dim.setdefault(q.dimension, []).append(q)

    for dim, qs in by_dim.items():
        if len(qs) < 2:
            continue
        # Across turns only. Two values in one answer are usually a derivation.
        worst = None
        for i in range(len(qs)):
            for j in range(i + 1, len(qs)):
                p, q = qs[i], qs[j]
                if p.turn == q.turn:
                    continue
                lo, hi = (p, q) if p.value <= q.value else (q, p)
                if lo.value <= 0:
                    continue
                spread = (hi.value - lo.value) / lo.value
                if spread > _RELATIVE_TOLERANCE and (
                        worst is None or spread > worst[0]):
                    worst = (spread, lo, hi)
        if worst is not None:
            _, lo, hi = worst
            a, b = (lo, hi) if lo.turn <= hi.turn else (hi, lo)
            report.divergences.append((dim, a, b))
    return report
