"""
tests/test_quantities.py — the cross-turn organ, against a real ledger.

The case is `/mnt/data/Codeberg/pn_vessel_llamacpp_c/vessel_data/ledgers/
granite-3.3-8b/20260320_164610.json` (2026-03-20, granite-3.3-8b): a session
that stated Voyager 1's distance as 24.2 billion kilometres on turn 1 and 14.2
billion miles on turn 4, with its own audit saying "Clear." both times. The
values are inlined here so the test runs without that tree present, and the
path is named so the original can be checked.

Run:  python3 tests/test_quantities.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from checks import quantities                                  # noqa: E402

VOYAGER = [
    (1, "As of the latest available data from web searches this year, the "
        "Voyager 1 spacecraft is approximately 24.2 billion kilometers away "
        "from Earth, traveling within the constellation Ophiuchus."),
    (2, "According to the most recent information provided by the fetched "
        "webpage, as of March 2026, Voyager 1 is located in the constellation "
        "Ophiuchus, at an approximate distance from Earth of 24.2 billion "
        "kilometers."),
    (3, "There seems to be a discrepancy because the provided search results "
        "do not contain specific information regarding the distance."),
    (4, "However, as of the last confirmed data from NASA (October 2021), "
        "Voyager 1 was approximately 14.2 billion miles from Earth."),
]

CONSISTENT = [
    (1, "Voyager 1 is approximately 24.2 billion kilometers from Earth."),
    (2, "That distance is about 24.2 billion kilometers, or roughly 162 au."),
]


def run():
    failures = []

    print("=" * 72)
    print("THE REAL VOYAGER LEDGER — four 'Clear.' verdicts passed this")
    print("=" * 72)
    r = quantities.check(VOYAGER)
    print(r.render())
    if not r.divergences:
        failures.append("the km-vs-miles divergence was NOT detected")
    else:
        proof = r.render()
        if "does NOT claim they refer to the same thing" not in proof:
            failures.append("the organ asserted coreference instead of "
                            "disclosing a difference")
        if "24.2 billion kilometers" not in proof or "14.2 billion miles" not in proof:
            failures.append("the original wording was not preserved in the report")

    print("\n" + "=" * 72)
    print("A CONSISTENT SESSION — must not be accused")
    print("=" * 72)
    r2 = quantities.check(CONSISTENT)
    print(r2.render())
    if r2.divergences:
        failures.append("a consistent session was falsely accused "
                        "(24.2 billion km vs 162 au are the same distance)")

    print("\n" + "=" * 72)
    print("NOTHING TO COMPARE — must report inapplicable, never consistent")
    print("=" * 72)
    r3 = quantities.check([(1, "Unicode assigns a number to each character.")])
    print(r3.render())
    if "not\nthe same as consistent" not in r3.render() and \
       "not the same as consistent" not in r3.render():
        failures.append("an inapplicable check reported as if consistent")

    print("\n" + "=" * 72)
    print("SAME-TURN DERIVATION — must not be accused")
    print("=" * 72)
    r4 = quantities.check([(1, "The bag is 84 kilograms. Each of four parts "
                                "is 21 kilograms.")])
    print(r4.render())
    if r4.divergences:
        failures.append("two masses in one answer were treated as a contradiction")
    if "pound" in quantities._UNITS or "lb" in quantities._UNITS:
        failures.append("pound/lb must not be a mass unit")

    print("\n" + "=" * 72)
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL PASS — the real cross-turn divergence is caught and disclosed")
    print("without asserting which value is wrong; a consistent session is not")
    print("accused; and having nothing to compare is not reported as agreement.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
