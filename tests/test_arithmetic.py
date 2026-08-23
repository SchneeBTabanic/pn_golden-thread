"""
tests/test_arithmetic.py — the checker, tested against the REAL failure.

Every string in TRANSCRIPT_CLAIMS is copied verbatim from
GTPS-Agent/pn_gtps-agent_test_terminal-output.txt — the live session of
2026-08-14 in which a governed agent made five false statements about the
letter 'r' and its own governance layer reported Phi=0.0178, every signal
clean. These are not invented test cases. They are the errors that got through.

Run:  python3 tests/test_arithmetic.py     (no pytest needed, no model, no server)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from checks.arithmetic import check, CONTRADICTED, CONFIRMED   # noqa: E402


# (verbatim sentence from the transcript, must_be_caught, note)
TRANSCRIPT_CLAIMS = [
    ("The Unicode code point for 'p' is 112.", False,
     "TRUE — 'p' is U+0070 = 112. Must NOT be accused."),

    ("The Unicode for the letter 'r' is U+0072. This is a 6-bit value, which "
     "can be represented in 6 bits.", True,
     "transcript line 231 — 'r' needs 8 bits, not 6"),

    ("In binary, it is represented as 01110010.", False,
     "TRUE and carries no claim to decide beyond the literal"),

    ("The '0x72' value corresponds to a 16-bit encoding (UTF-16), which would "
     "be represented as two bytes: 0x72 0x72.", True,
     "transcript line 238 — 'r' in UTF-16 is 0x00 0x72, never 0x72 0x72"),

    ("In this case, there are 8 '1's, which means the character 'r' in Unicode "
     "requires 8 bits.", False,
     "transcript line 467, IN ISOLATION — genuinely undecidable: the field it "
     "counts is in an earlier sentence. Must NOT be accused here. The "
     "whole-answer path below proves it IS caught in context."),

    ("The binary representation of 'r' is 01110010, which consists of 6 bits.", True,
     "transcript line 701 — it consists of 8"),

    ("The binary representation of 'r' is 01110010, which translates to 114 in "
     "the decimal system, corresponding to the Unicode code point U+0072.", False,
     "transcript line 706 — this one is TRUE. Must NOT be accused."),

    ("The binary representation of the Unicode character 'r' is 01110010. This "
     "binary sequence is composed of 6 bits.", True,
     "transcript line 816 — 8, not 6"),

    ("The binary number 01110010 is 6 bits long, but it represents a value "
     "greater than what can be stored in 6 or 8 bits.", True,
     "transcript line 907 — the PROXY said this, laundered as 'the diagnostics show'"),
]


def run():
    failures = []
    print("=" * 74)
    print("CHECKING THE REAL 2026-08-14 SESSION, SENTENCE BY SENTENCE")
    print("=" * 74)

    for sentence, must_catch, note in TRANSCRIPT_CLAIMS:
        rep = check(sentence)
        caught = bool(rep.contradicted)
        ok = (caught == must_catch)
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failures.append((sentence, must_catch, caught, note))
        print(f"\n[{mark}] {note}")
        print(f'       "{sentence[:88]}{"…" if len(sentence) > 88 else ""}"')
        for v in rep.contradicted:
            print(f"       CAUGHT -> {v.proof}")
        for v in rep.confirmed:
            print(f"       confirmed -> {v.proof}")
        if must_catch and not caught:
            print("       *** THIS ERROR WOULD STILL GET THROUGH ***")
        if caught and not must_catch:
            print("       *** FALSE ACCUSATION — worse than a miss ***")

    # The whole-answer path: the actual multi-sentence answer from turn 5.
    print("\n" + "=" * 74)
    print("WHOLE-ANSWER PATH — transcript turn 5 (lines 464-476), verbatim")
    print("=" * 74)
    turn5 = (
        "The binary representation of the Unicode character 'r' is 01110010.\n"
        "To find the number of bits, simply count the number of '1's in the "
        "binary sequence.\n"
        "In this case, there are 8 '1's, which means the character 'r' in "
        "Unicode requires 8 bits.\n"
        "As for starting counting bits, you can begin at the leftmost '1' (the "
        "most significant bit) and count each subsequent '1' to the right.\n"
    )
    rep = check(turn5)
    print(rep.render())
    if not rep.contradicted:
        failures.append(("turn-5 whole answer", True, False,
                         "the answer that taught him to count bits by counting 1s"))
        print("*** THE TURN-5 ANSWER WOULD STILL PASS UNCHECKED ***")

    # Silence must never read as clearance.
    print("\n" + "=" * 74)
    print("REACH DISCIPLINE — an answer with nothing decidable in it")
    print("=" * 74)
    rep = check("Unicode is a standard for representing text in computers.")
    print(rep.render())
    if "not the same as clean" not in rep.render():
        failures.append(("reach statement", True, False,
                         "silence was allowed to read as clearance"))

    print("\n" + "=" * 74)
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for s, must, got, note in failures:
            print(f"  - {note}\n      expected caught={must}, got caught={got}")
        return 1
    print("ALL PASS — every false statement from the real session is caught,")
    print("and the two true statements are not accused.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
