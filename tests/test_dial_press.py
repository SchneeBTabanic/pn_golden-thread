#!/usr/bin/env python3
"""Phase 5b/5c: /dial and /press. Off by default. No model."""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import examine  # noqa: E402
import run as runmod  # noqa: E402
import turn_record  # noqa: E402


HOLD_BANNER = (
    "[HELD — testimony placed by the human, in stasis. Not fact, not error.\n"
    "Do not adopt it. Do not argue it away. Answer from yourself.\n"
    "If your answer contradicts it, say so plainly and leave it held.\n"
    "It is released only by the human, never by an answer.]"
)

DIAL_FRAG = "toward the placed span — a force you set, not a judgment"
PRESS_FRAG = "— a hand you placed, not a judgment"


def run():
    fails = []
    if turn_record.HOLD_BANNER != HOLD_BANNER:
        fails.append("HOLD_BANNER was modified — it is not to be touched")
    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    model_src = open(os.path.join(HERE, "model.py"), encoding="utf-8").read()
    if DIAL_FRAG not in src:
        fails.append("dial loud line drifted")
    if PRESS_FRAG not in src:
        fails.append("press loud line drifted")
    if runmod.DIAL_NEED_SPAN != "/dial needs something placed to lean on":
        fails.append("dial need-span refusal drifted")
    if runmod.PRESS_NEED_SPAN != "/press needs a placed span to put a hand on":
        fails.append("press need-span refusal drifted")
    if "Two forces at once cannot be attributed." not in runmod.DIAL_BOTH_REFUSE:
        fails.append("dial+press refuse drifted")
    if 'low == "/dial"' not in src and 'low.startswith("/dial")' not in src:
        fails.append("/dial command missing")
    if 'low == "/press"' not in src and 'low.startswith("/press")' not in src:
        fails.append("/press command missing")
    if "gt_dial" in model_src.split("def probe_measured", 1)[1].split(
            "def executor_prompt", 1)[0]:
        fails.append("probe_measured carries gt_dial")
    if "gt_press" in model_src.split("def probe_measured", 1)[1].split(
            "def executor_prompt", 1)[0]:
        fails.append("probe_measured carries gt_press")
    kind, val = runmod.parse_dial_cmd("/dial off")
    if kind != "off":
        fails.append("parse /dial off: " + repr((kind, val)))
    kind, val = runmod.parse_dial_cmd("/dial 0.5")
    if kind != "on" or val != "0.5":
        fails.append("parse /dial 0.5: " + repr((kind, val)))
    kind, val = runmod.parse_dial_cmd("/dial 0")
    if kind != "off":
        fails.append("/dial 0 should be off")
    kind, val = runmod.parse_dial_cmd("/dial")
    if kind != "err":
        fails.append("bare /dial should err")
    kind, s, sp = runmod.parse_press_cmd("/press off")
    if kind != "off":
        fails.append("parse /press off: " + repr((kind, s, sp)))
    kind, s, sp = runmod.parse_press_cmd("/press 0.01 file")
    if kind != "on" or s != "0.01" or sp != "file":
        fails.append("parse /press 0.01 file: " + repr((kind, s, sp)))
    kind, s, sp = runmod.parse_press_cmd("/press 1 file")
    if kind != "on" or s != "1" or sp != "file":
        fails.append("parse /press 1 file: " + repr((kind, s, sp)))
    a_old = runmod.press_pasta_alpha("4.605170185988091")
    if a_old is None or abs(a_old - 0.01) > 1e-6:
        fails.append("old 0.01 force should be S≈4.605: " + repr(a_old))
    a_tiny = runmod.press_pasta_alpha("0.01")
    if a_tiny is None or a_tiny < 0.98:
        fails.append("new 0.01 must be weak (α near 1), got " + repr(a_tiny))
    a1 = runmod.press_pasta_alpha("1")
    a2 = runmod.press_pasta_alpha("2")
    if not (a2 < a1 < 1.0):
        fails.append("larger S must send smaller PASTA α (stronger exclude)")
    kind, s, sp = runmod.parse_press_cmd("/press")
    if kind != "err":
        fails.append("bare /press should err")
    if examine.dial_clock("") != "":
        fails.append("off dial clock is not silent")
    if examine.press_clock("", "") != "":
        fails.append("off press clock is not silent")
    if runmod.dial_loud("0.5") != (
            "── dialed: α=0.5 toward the placed span — a force you set, "
            "not a judgment ──"):
        fails.append("dial_loud drifted: " + repr(runmod.dial_loud("0.5")))
    if runmod.press_loud("0.01", "file") != (
            "── pressed: 0.01 on file — a hand you placed, not a judgment ──"):
        fails.append("press_loud drifted: "
                     + repr(runmod.press_loud("0.01", "file")))
    reg = json.loads(open(
        os.path.join(HERE, "tag_register.json"), encoding="utf-8").read())
    for key in ("relied", "dialed", "pressed"):
        if key not in reg.get("keys", {}):
            fails.append("tag_register missing witness " + key)
        elif reg["keys"][key].get("kind") != "witness":
            fails.append(key + " is not a witness key")
    if "extra_tags=None" not in src:
        fails.append("run.py must still record turns with extra_tags=None")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — dial and press off by default; refusals named; probe clean")
    return 0


if __name__ == "__main__":
    sys.exit(run())
