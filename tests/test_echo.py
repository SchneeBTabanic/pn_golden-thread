"""
tests/test_echo.py — the prompt-echo detector against the real 2026-08-14 echo.

The answer text is copied verbatim from
GTPS-Agent/pn_gtps-agent_test_terminal-output.txt lines 172-184, where the
model answered "What is the Unicode for 'r'" and then printed two clause
definitions out of its own system prompt as the body of the answer.

Run:  python3 tests/test_echo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from checks import echo                                     # noqa: E402

# Exactly what agent.py:482 builds: f"\n\n--- {u.name} ---\n{body}"
DELIVERED = {
    "Clause 21: Output Provenance Tagging":
        "Tag outputs with confidence level and source category.",
    "Clause 4: Prohibition on Reliance on Cached Data and Probabilistic Shortcuts":
        "Avoid cached drafts or statistical shortcuts for critical outputs to "
        "prevent corruption.\n"
        "Allow user-approved caching for non-critical outputs.\n"
        "Regenerate critical deliverables from scratch.",
}

# transcript lines 172-184, verbatim
ECHOING_ANSWER = """\
The Unicode for the letter 'r' is U+0072.

--- Clause 21: Output Provenance Tagging ---
Tag outputs with confidence level and source category.

--- Clause 4: Prohibition on Reliance on Cached Data and Probabilistic Shortcuts ---
Avoid cached drafts or statistical shortcuts for critical outputs to prevent corruption.
Allow user-approved caching for non-critical outputs.
Regenerate critical deliverables from scratch.
"""

CLEAN_ANSWER = """\
The Unicode code point for the letter 'r' is U+0072, which is 114 in decimal.
It is one byte in UTF-8.
"""

# The case a shape-matching filter would get WRONG: the human asked ABOUT the
# clause, so the model discusses it in its own words. Nothing is copied, and
# nothing must be flagged. This is why the check is exact-match against what
# was delivered, and never a pattern like "--- Clause \\d+".
DISCUSSING_ANSWER = """\
Clause 21 asks you to tag an output with how confident you are and where the
content came from. In practice that means naming the source category rather
than leaving the reader to guess it.
"""


def run():
    failures = []

    r = echo.check(ECHOING_ANSWER, DELIVERED)
    print("=" * 72)
    print("THE REAL ECHO — transcript lines 172-184")
    print("=" * 72)
    print(r.render())
    if not r.found:
        failures.append("the real clause echo was NOT detected")
    elif len(r.echoed) < 3:
        failures.append(f"only {len(r.echoed)} echoed lines found, expected >=3")

    print("\n" + "=" * 72)
    print("A CLEAN ANSWER — must not be accused")
    print("=" * 72)
    r2 = echo.check(CLEAN_ANSWER, DELIVERED)
    print(r2.render())
    if r2.found:
        failures.append("clean answer was falsely accused of echoing")

    print("\n" + "=" * 72)
    print("DISCUSSING THE CLAUSE IN ITS OWN WORDS — must not be accused")
    print("=" * 72)
    r3 = echo.check(DISCUSSING_ANSWER, DELIVERED)
    print(r3.render())
    if r3.found:
        failures.append("a legitimate discussion of the clause was accused — "
                        "this is what a shape-matching filter would get wrong")

    print("\n" + "=" * 72)
    print("NOTHING DELIVERED — must report inapplicable, never clean")
    print("=" * 72)
    r4 = echo.check(CLEAN_ANSWER, {})
    print(r4.render())
    if "not a clean result" not in r4.render().lower().replace("—", "—"):
        if "Not a clean result" not in r4.render():
            failures.append("an inapplicable check reported as if it were clean")

    print("\n" + "=" * 72)
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL PASS — the real echo is caught, and neither a clean answer nor a")
    print("legitimate discussion of the same clause is falsely accused.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
