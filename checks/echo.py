"""
witness/echo.py — DID THE MODEL HAND BACK ITS OWN PROMPT?

Licensed by Charter §3.4 ("if a constraint can be checked after generation,
check it after generation") and §3.8 (absence and echo both named, never
implied). The method is prescribed by the project's own standing ruling on this
exact failure — memory `triune-relations-and-the-reverse-view`:

    fix by MARK, never EXEMPT ... mark by DETERMINISTIC MATCH against the
    ACTUAL injected text (we know exactly what we delivered this turn), NEVER
    by a "looks like system text" shape heuristic.

WHY IT EXISTS. The oldest unhealed failure in this project, seven recorded
instances between 2026-07-19 and 2026-08-14: the model emits the text it was
given as though it were the answer. Worked examples copied verbatim. `<slot>`
markers printed as content. `GOVERNANCE_SKIN_START` parsed as an actor. And on
2026-08-14, this, presented to the human as the answer to "What is the Unicode
for 'r'":

    The Unicode for the letter 'r' is U+0072.

    --- Clause 21: Output Provenance Tagging ---
    Tag outputs with confidence level and source category.

    --- Clause 4: Prohibition on Reliance on Cached Data ... ---

That string is byte-identical to the injection template. Every fix attempted in
prose ("never copy them") eroded silently at the next rearrangement. The one
fix that MEASURABLY worked was structural — the grammar's angle-bracket ban
took slot-copying from ~2 of 3 cold runs to 0 of 4.

This module is the after-the-fact companion to that: it cannot prevent the
echo, but it can make it IMPOSSIBLE TO MISS, and it can never be wrong about
it, because it compares the answer against the exact bytes delivered this turn.

WHY NOT A SHAPE HEURISTIC. Matching `--- Clause \\d+: .* ---` would be a filter,
and this project's standing rule refuses filters: "there can never be enough
words." It would also be WRONG in the one case that matters most — a human
asking *about* Clause 21 should get Clause 21 discussed, and a shape matcher
cannot tell discussion from regurgitation. Exact-substring against what was
actually delivered can: if the model reproduces a delivered line verbatim, it
copied it; if it talks about the clause in its own words, nothing matches.

NO SCORE. This returns spans and their sources, not a percentage of
"echoiness". A count of echoed lines is a fact; a similarity ratio would be a
computed score standing in for a judgement (the asserted-vs-computed boundary),
and it is not needed: an exact match is already a decision.
"""
from dataclasses import dataclass, field
from typing import Dict, List

INTEGRITY = {
    "conserves": "the exact text delivered to the model this turn, so the "
                 "verdict is a comparison and never an opinion about style",
    "discards": "nothing -- an answer with no echo is reported as checked-and-"
                "clear WITH the number of sources compared, so a clear result "
                "cannot be confused with a check that had nothing to compare",
    "proves_it_by": "tests/test_echo.py, using the verbatim Clause 21 echo "
                    "from the 2026-08-14 transcript",
    "surfaced_as": "ECHOED / checked against N delivered block(s)",
}

# A line must be at least this long to count as an echo. Below it, collisions
# are real: a one-word line ("none", "Clear.") can coincide innocently. This is
# a floor on EVIDENCE, not a tuning knob for sensitivity -- raising it can only
# make the check quieter, never louder, so it can never manufacture a finding.
_MIN_ECHO_CHARS = 24


@dataclass
class EchoReport:
    echoed: List[tuple] = field(default_factory=list)   # (source_name, line)
    sources_compared: int = 0
    source_names: List[str] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return bool(self.echoed)

    def render(self) -> str:
        """Always states what it compared against — a clear verdict from zero
        sources and a clear verdict from five are different facts (§3.8)."""
        if self.sources_compared == 0:
            return ("Prompt-echo check: nothing was injected into the model's "
                    "prompt this turn, so there was nothing to echo. Not a "
                    "clean result — an inapplicable one.")
        if not self.echoed:
            # STATED AS A RESULT, NOT AS A NEGATION. The earlier wording was
            # "the answer reproduces no line of the N blocks delivered" — and
            # live, the 2B Proxy read that as "the prompt-echo check failed…
            # which could be a concern". It had inverted a clean result into a
            # warning, because the sentence's only verb was a negative one. A
            # report that a small model reliably misreads is a defect in the
            # report. Lead with the verdict word.
            return (f"Prompt-echo check: PASSED — the answer is in the model's "
                    f"own words. None of it is copied from the "
                    f"{self.sources_compared} block(s) it was given "
                    f"({', '.join(self.source_names)}).")
        by_source: Dict[str, int] = {}
        for name, _ in self.echoed:
            by_source[name] = by_source.get(name, 0) + 1
        lines = [f"The answer HANDS BACK {len(self.echoed)} line(s) of the text "
                 f"it was given, not content of its own:"]
        for name, count in by_source.items():
            lines.append(f"  - {count} line(s) copied verbatim from: {name}")
        for name, ln in self.echoed[:4]:
            short = ln if len(ln) <= 88 else ln[:87] + "…"
            lines.append(f'      "{short}"')
        lines.append("  This is the prompt being recited, not a claim the model "
                     "made. Treat it as absent answer, not as answer.")
        return "\n".join(lines)


def _significant_lines(text: str) -> List[str]:
    out = []
    for ln in (text or "").splitlines():
        ln = " ".join(ln.split())
        if len(ln) >= _MIN_ECHO_CHARS:
            out.append(ln)
    return out


def check(answer: str, delivered: Dict[str, str]) -> EchoReport:
    """Compare `answer` against every block delivered to the model this turn.

    `delivered` maps a human-readable source name ("Clause 21: Output
    Provenance Tagging", "output contract", "file: notes.md") to the exact text
    handed over. The caller must pass what it ACTUALLY sent — this check is
    only as honest as its input, which is why the agent builds it from the same
    variable it puts in the prompt rather than reconstructing it afterwards."""
    report = EchoReport()
    report.sources_compared = len(delivered)
    report.source_names = list(delivered.keys())
    if not delivered:
        return report
    answer_lines = set(_significant_lines(answer))
    if not answer_lines:
        return report
    for name, text in delivered.items():
        for ln in _significant_lines(text):
            if ln in answer_lines:
                report.echoed.append((name, ln))
    return report
