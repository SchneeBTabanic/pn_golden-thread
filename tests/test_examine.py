#!/usr/bin/env python3
"""Clock, not sermon."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import examine  # noqa: E402
import law as law_module  # noqa: E402


def run():
    fails = []
    law = law_module.load()
    none = examine.clock("")
    got = examine.clock("/tmp/x")
    if none != "FETCHED: none":
        fails.append(f"empty clock: {none!r}")
    if got != "FETCHED: /tmp/x":
        fails.append(f"path clock: {got!r}")
    if examine.held_clock(0) != "HELD: none":
        fails.append(f"held none: {examine.held_clock(0)!r}")
    if examine.held_clock(2) != "HELD: 2 in stasis":
        fails.append(f"held n: {examine.held_clock(2)!r}")
    if examine.probe_clock(True) != (
            "PROBE: rendered — byte-identical to the answer"):
        fails.append(f"probe same: {examine.probe_clock(True)!r}")
    if examine.probe_clock(False) != (
            "PROBE: rendered — not byte-identical to the answer"):
        fails.append(f"probe diff: {examine.probe_clock(False)!r}")
    if examine.dial_clock("") != "":
        fails.append("dial clock off must be silent: "
                     + repr(examine.dial_clock("")))
    if examine.dial_clock("0.5") != "DIAL: 0.5":
        fails.append("dial clock drifted: " + repr(examine.dial_clock("0.5")))
    if examine.press_clock("", "file") != "":
        fails.append("press clock off must be silent")
    if examine.press_clock("0.01", "file") != "PRESS: 0.01 on file":
        fails.append("press clock drifted: "
                     + repr(examine.press_clock("0.01", "file")))
    if not examine.probe_same("2 + 2 equals 4.", "2+2equals4."):
        fails.append("whitespace-stripped equality failed")
    if examine.probe_same("4", "2"):
        fails.append("divergent answers compared equal")
    findings = examine.examine(
        answer="2 + 2 equals 5.", delivered={}, session_answers=[],
        fetched_from="", model_self_audit="Clear.")
    text = examine.render(findings, law)
    if text != "FETCHED: none":
        fails.append(f"render: {text!r}")
    for bad in ("training probability", "Clear", "YOUR LAW", "DID NOT APPLY",
                "decidable", "prompt-echo"):
        if bad in text:
            fails.append(f"sermon leaked: {bad!r}")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — clock only; no sermon")
    return 0


if __name__ == "__main__":
    sys.exit(run())
