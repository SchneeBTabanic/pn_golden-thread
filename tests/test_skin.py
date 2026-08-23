#!/usr/bin/env python3
"""Skin parser has no Whistleblower slot. Grammar cannot emit one."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import run as runmod  # noqa: E402


def run():
    fails = []
    raw = (
        "ANSWER_START\n"
        "[EXECUTOR]\n"
        "Two plus two equals four.\n"
        "ANSWER_END\n"
    )
    answer, absent, held = runmod.parse_skin(raw)
    if answer != "Two plus two equals four.":
        fails.append(f"parse_skin lost the answer: {answer!r}")
    if absent:
        fails.append("a real answer was marked absent")
    if held:
        fails.append("default skin produced a held seat: " + repr(held))
    short = (
        "ANSWER_START\n"
        "[EXECUTOR]\n"
        "Four.\n"
        "ANSWER_END\n"
    )
    a3, absent3, h3 = runmod.parse_skin(short)
    if a3 != "Four." or absent3:
        fails.append(f"short answer treated as absent: {a3!r} absent={absent3}")
    if h3:
        fails.append("short skin produced a held seat: " + repr(h3))
    # A leftover [WHISTLEBLOWER] line must not be treated as a section.
    raw2 = (
        "ANSWER_START\n"
        "[EXECUTOR]\n"
        "hello\n"
        "[WHISTLEBLOWER]\n"
        "Clear.\n"
        "ANSWER_END\n"
    )
    answer2, _absent2, held2 = runmod.parse_skin(raw2)
    if "Clear" in answer2:
        fails.append("Whistleblower text was accepted as the answer")
    if "Clear" in held2:
        fails.append("Whistleblower text was accepted as the held seat")
    # It will currently be treated as body because [WHISTLEBLOWER] is not a
    # marker. That is wrong if someone leaves the old grammar on disk.
    # The grammar file itself must not contain the section.
    g = open(os.path.join(HERE, "grammar.gbnf"), encoding="utf-8").read()
    if "WHISTLEBLOWER" in g.split("#")[0] or "whistleblower-section" in g:
        # comments may mention it; the rule name must be gone
        rules = [ln for ln in g.splitlines()
                 if ln.strip() and not ln.strip().startswith("#")]
        if any("WHISTLEBLOWER" in ln or "whistleblower" in ln for ln in rules):
            fails.append("grammar still has a whistleblower rule")
    c = open(os.path.join(HERE, "contract.txt"), encoding="utf-8").read()
    if "[WHISTLEBLOWER]" in c:
        fails.append("contract still invites a Whistleblower line")
    if '"Clear." is a fine' in c or "Clear. is a fine" in c:
        fails.append("contract still licenses Clear.")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — skin is answer-only; Clear. is not invited")
    return 0


if __name__ == "__main__":
    sys.exit(run())
