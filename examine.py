"""
examine.py — the clock, not the sermon.

Room A: every turn a boring mark of what was looked up.
Loud language ("training probability", the 48-clause ledger, Clause 46
unreached) taught him to stop reading. Those live on /law and in the
pile, not on every turn.

Clause 21 is still the licence. The mark is FETCHED: none | FETCHED: path.
"""
from dataclasses import dataclass
from typing import List, Optional

INTEGRITY = {
    "conserves": "what was looked up this turn, as a clock",
    "discards": "the sermon that fired on every chat turn",
    "proves_it_by": "tests/test_examine.py",
    "surfaced_as": "one line on stderr",
}

PASS = "PASS"
FAIL = "FAIL"
DID_NOT_APPLY = "DID NOT APPLY"
UNCITED = None


@dataclass
class Finding:
    check: str
    verdict: str
    clause: Optional[str]
    detail: str
    reach: str
    note: str = ""

    def __post_init__(self):
        if not self.reach.strip():
            raise ValueError(f"{self.check}: no reach stated (Clause 30).")


def clock(fetched_from: str) -> str:
    """The only line stderr should say about provenance, every turn."""
    if fetched_from:
        return "FETCHED: " + fetched_from
    return "FETCHED: none"


def held_clock(n):
    """How many holds are in stasis. Absence is none, never a missing line."""
    n = int(n or 0)
    if n:
        return "HELD: " + str(n) + " in stasis"
    return "HELD: none"


def whitespace_stripped(s):
    """All whitespace removed. The only equality probe is allowed."""
    return "".join((s or "").split())


def probe_same(rendered, answered):
    return whitespace_stripped(rendered) == whitespace_stripped(answered)


def probe_clock(identical):
    """PROBE clock. Absence of a match is named, never silent."""
    if identical:
        return "PROBE: rendered — byte-identical to the answer"
    return "PROBE: rendered — not byte-identical to the answer"


def dial_clock(alpha):
    """Only emitted while the dial is on. Off is silence, not DIAL: off."""
    if not alpha:
        return ""
    return "DIAL: " + str(alpha)


def press_clock(strength, span):
    """Only emitted while the press is on. Off is silence, not PRESS: off."""
    if not strength or not span:
        return ""
    return "PRESS: " + str(strength) + " on " + str(span)


# RELIED says where attention mass went, not whether the answer is
# faithful or true.


def examine(answer: str, delivered: dict, session_answers: list,
            fetched_from: str, model_self_audit: str) -> List[Finding]:
    del answer, delivered, session_answers, model_self_audit
    if fetched_from:
        detail = clock(fetched_from)
        reach = "This says what was FETCHED, not whether the answer used it."
    else:
        detail = clock("")
        reach = "This says what was FETCHED, not whether the answer is true."
    return [Finding(
        check="provenance", verdict=PASS, clause="21",
        detail=detail, reach=reach)]


def render(findings: List[Finding], law) -> str:
    """Clock only. law is accepted so callers do not grow a second signature."""
    del law
    for f in findings:
        if f.check == "provenance":
            return f.detail
    return "FETCHED: none"
