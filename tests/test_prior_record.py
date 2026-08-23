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
    if "/forget" not in status or "window:" not in status:
        fails.append("window clock lost its refuseable English: " + repr(status))
    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if "hist = None if skin_on else pairs" in src:
        fails.append("unmasked talk still feeds Granite role-history")
    if "hist = None" not in src:
        fails.append("hist = None missing")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — prior record is ASKED/ANSWERED under dividers, not roles")
    return 0


if __name__ == "__main__":
    sys.exit(run())
