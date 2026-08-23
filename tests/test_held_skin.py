#!/usr/bin/env python3
"""5a: [HELD] grammar seat. Original pair untouched. Off unless flagged."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import run as runmod  # noqa: E402
import turn_record  # noqa: E402


BANNER = (
    "[HELD — testimony placed by the human, in stasis. Not fact, not error.\n"
    "Do not adopt it. Do not argue it away. Answer from yourself.\n"
    "If your answer contradicts it, say so plainly and leave it held.\n"
    "It is released only by the human, never by an answer.]"
)

HELD_LOUD = (
    "── skin: [HELD] seat — GT_HELD_SKIN=1, not the default pair ──"
)


def _rules(text):
    return [ln for ln in text.splitlines()
            if ln.strip() and not ln.strip().startswith("#")]


def run():
    fails = []
    if turn_record.HOLD_BANNER != BANNER:
        fails.append("HOLD_BANNER was modified — it must stay verbatim")
    g = open(os.path.join(HERE, "grammar.gbnf"), encoding="utf-8").read()
    c = open(os.path.join(HERE, "contract.txt"), encoding="utf-8").read()
    gh = open(os.path.join(HERE, "grammar_held.gbnf"), encoding="utf-8").read()
    ch = open(os.path.join(HERE, "contract_held.txt"), encoding="utf-8").read()
    g_rules = _rules(g)
    h_rules = _rules(gh)
    if any("held-section" in ln or '"[HELD]"' in ln for ln in g_rules):
        fails.append("original grammar.gbnf grew a [HELD] rule")
    if "[HELD]" in c:
        fails.append("original contract.txt invites a [HELD] section")
    if not any("held-section" in ln for ln in h_rules):
        fails.append("grammar_held.gbnf has no held-section rule")
    if not any("[HELD]" in ln for ln in h_rules):
        fails.append("grammar_held.gbnf does not emit [HELD]")
    if "[HELD]" not in ch:
        fails.append("contract_held.txt does not name the [HELD] seat")
    if '"Clear." is a fine' in ch or "Clear. is a fine" in ch:
        fails.append("contract_held still licenses Clear.")
    if "Do not write \"Clear.\"" not in ch:
        fails.append("contract_held dropped the Clear. ban")
    try:
        runmod._check_grammar_one_line_per_rule(gh, "grammar_held.gbnf")
    except SystemExit as e:
        fails.append("grammar_held one-line guard: " + str(e))
    raw = (
        "ANSWER_START\n"
        "[EXECUTOR]\n"
        "Four.\n"
        "[HELD]\n"
        "This answer contradicts the testimony.\n"
        "ANSWER_END\n"
    )
    answer, absent, held = runmod.parse_skin(raw)
    if answer != "Four.":
        fails.append("held-skin lost the answer: " + repr(answer))
    if absent:
        fails.append("held-skin marked a real answer absent")
    if held != "This answer contradicts the testimony.":
        fails.append("held seat not extracted: " + repr(held))
    raw2 = (
        "ANSWER_START\n"
        "[EXECUTOR]\n"
        "hello\n"
        "[WHISTLEBLOWER]\n"
        "Clear.\n"
        "ANSWER_END\n"
    )
    a2, _abs2, h2 = runmod.parse_skin(raw2)
    if "Clear" in a2 or "Clear" in h2:
        fails.append("Whistleblower text leaked into answer or held seat")
    raw3 = (
        "ANSWER_START\n"
        "[EXECUTOR]\n"
        "Two plus two equals four.\n"
        "ANSWER_END\n"
    )
    a3, abs3, h3 = runmod.parse_skin(raw3)
    if a3 != "Two plus two equals four." or abs3 or h3:
        fails.append("original-shape skin drifted: "
                     + repr((a3, abs3, h3)))
    old = os.environ.get("GT_HELD_SKIN")
    try:
        os.environ.pop("GT_HELD_SKIN", None)
        if runmod.held_skin_wanted(1):
            fails.append("held pair selected with GT_HELD_SKIN unset")
        os.environ["GT_HELD_SKIN"] = "1"
        if runmod.held_skin_wanted(0):
            fails.append("held pair selected with no holds")
        if not runmod.held_skin_wanted(1):
            fails.append("held pair not selected when flagged and holds live")
        os.environ["GT_HELD_SKIN"] = "0"
        if runmod.held_skin_wanted(2):
            fails.append("held pair selected with GT_HELD_SKIN=0")
    finally:
        if old is None:
            os.environ.pop("GT_HELD_SKIN", None)
        else:
            os.environ["GT_HELD_SKIN"] = old
    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if HELD_LOUD not in src:
        fails.append("held-skin loud line drifted")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — held skin is a flagged pair; original pair untouched")
    return 0


if __name__ == "__main__":
    sys.exit(run())
