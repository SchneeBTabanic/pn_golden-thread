#!/usr/bin/env python3
"""B wrap: last-N as ASKED/ANSWERED under clerk dividers, not chat roles."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import run as runmod  # noqa: E402


def run():
    fails = []
    if runmod.PRIOR_RECORD != (
            "── prior record (diary, last turns, arrival order — "
            "not the line just typed) ──"):
        fails.append("PRIOR_RECORD drifted")
    if runmod.LIVE_MOUTH != "── live mouth (the human's question now) ──":
        fails.append("LIVE_MOUTH drifted")
    if runmod.PRIOR_RECORD_END != (
            "── end of that record (not the line just typed) ──"):
        fails.append("PRIOR_RECORD_END drifted")
    blocks = [
        {"body": "ASKED:\nWhat is 2+2?\n\nANSWERED:\n4.\n"},
        {"body": "ASKED:\nping\n\nANSWERED:\n1. The Cathedral Principle\n"},
    ]
    slab = runmod.prior_record_slab(blocks)
    if "What is 2+2?" not in slab or "Cathedral" not in slab:
        fails.append("slab lost bodies: " + repr(slab[:200]))
    if "@@ " in slab:
        fails.append("B slab grew pile headers — that is arm C")
    ends = slab.count(runmod.PRIOR_RECORD_END)
    if ends != 2:
        fails.append("each prior record must close: " + repr(ends))
    ping_at = slab.find("Cathedral")
    end_after = slab.find(runmod.PRIOR_RECORD_END, ping_at)
    if end_after < 0:
        fails.append("Cathedral recitation was not closed")
    status = runmod.window_status()
    if "/forget" not in status:
        fails.append("window clock lost /forget: " + repr(status))
    if runmod.standing_history_mode() != "raw":
        fails.append("talk default is not raw: "
                     + repr(runmod.standing_history_mode()))
    if "divider family" not in status and "GT_SCORE_HISTORY=none" not in status:
        fails.append("window does not name standing last-N: " + repr(status))
    if "^ fold" not in status and "GT_SCORE_HISTORY" not in status:
        fails.append("R2 placement not named: " + repr(status))
    old = os.environ.get("GT_SCORE_HISTORY")
    os.environ["GT_SCORE_HISTORY"] = "none"
    try:
        if runmod.standing_history_mode() != "none":
            fails.append("none no longer isolates")
        none_status = runmod.window_status()
        if "PLACED: none" not in none_status:
            fails.append("lab none lost PLACED: none: " + repr(none_status))
    finally:
        if old is None:
            os.environ.pop("GT_SCORE_HISTORY", None)
        else:
            os.environ["GT_SCORE_HISTORY"] = old
    if runmod.score_clock("none", 0, 1) != "PLACED: none · hold(1)":
        fails.append("score clock none drifted: "
                     + repr(runmod.score_clock("none", 0, 1)))
    if runmod.score_clock("fold", 4, 1) != "PLACED: fold(4) · hold(1)":
        fails.append("score clock fold drifted: "
                     + repr(runmod.score_clock("fold", 4, 1)))
    rec = runmod.fold_recap("辻1", blocks)
    if "clerk recap" not in rec or "Cathedral" not in rec:
        fails.append("fold recap lost minutes: " + repr(rec[:200]))
    if rec.startswith("ASKED:"):
        fails.append("fold recap is raw ASKED labels")
    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if "hist = None if skin_on else pairs" in src:
        fails.append("unmasked talk still feeds Granite role-history")
    if "hist = None" not in src:
        fails.append("hist = None missing")
    if "place_mode" not in src or "parse_score_place" not in src:
        fails.append("R2 placement path missing")
    if "if keep and not self.skin_on" in src:
        fails.append("ambient last-N wrap is back")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — R1/R2: last-N only when placed; fold is clerk minutes")
    return 0


if __name__ == "__main__":
    sys.exit(run())
