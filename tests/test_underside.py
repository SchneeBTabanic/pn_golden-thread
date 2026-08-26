#!/usr/bin/env python3
"""C3: the boundary split. The straddling step is KEPT and excluded, never apportioned."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import relied  # noqa: E402
from tape import split_tape  # noqa: E402


def _series(blens, vals, prefix=0):
    return {"scale": 10000, "prefix_bytes": prefix, "bytes": blens,
            "spans": {"asked": vals}}


def run():
    fails = []
    S = 10000

    # clean split: 3 steps of 2 bytes, prefix 0, cut at 4 -> 2 face, 1 under
    p, note = relied.split_series(_series([2, 2, 2], [3300, 3300, 500]), 4, 6)
    if p is None:
        fails.append("clean split refused: " + note)
    else:
        if len(p["face"]["asked"]) != 2 or len(p["underside"]["asked"]) != 1:
            fails.append("clean split seated steps wrongly")
        if p["boundary_count"] != 0:
            fails.append("no straddle should mean boundary_count 0")

    # the straddle: cut falls INSIDE step 1 (bytes 2..7), kept not apportioned
    p, _ = relied.split_series(_series([2, 5, 2], [3300, 2000, 400]), 4, 9)
    if p is None:
        fails.append("straddle case refused")
    else:
        if p["boundary_count"] != 1 or p["boundary_index"] != 1:
            fails.append("straddling step not identified")
        if p["boundary"].get("asked") != 2000:
            fails.append("straddling READING was lost — the ruling keeps it")
        if 2000 in p["face"]["asked"] or 2000 in p["underside"]["asked"]:
            fails.append("straddling step leaked into a derived profile")
        if len(p["face"]["asked"]) != 1 or len(p["underside"]["asked"]) != 1:
            fails.append("straddle seating wrong")

    # prefix_bytes shifts the walk: the unmeasured first token is before step 0
    p, _ = relied.split_series(_series([2, 2], [3300, 500], prefix=3), 5, 7)
    if p is None or len(p["face"]["asked"]) != 1:
        fails.append("prefix_bytes did not shift the walk")
    if p and p["unmeasured_prefix_bytes"] != 3:
        fails.append("unmeasured prefix not disclosed")

    # a series that does not reconcile is REFUSED, never walked
    p, note = relied.split_series(_series([2, 2], [1, 1]), 2, 99)
    if p is not None or note != relied.NO_SPLIT:
        fails.append("unreconciled series was walked instead of refused")

    # cut_byte None is a named refusal, never treated as zero
    p, note = relied.split_series(_series([2], [1]), None, 2)
    if p is not None or note != relied.NO_CUT:
        fails.append("cut_byte None must be a named refusal, not offset 0")

    # returns count EVENTS, not steps: a run above the mark counts once
    if relied.count_returns([3400, 3400, 3400], S) != 1:
        fails.append("a single run above the mark should be one return")
    if relied.count_returns([3400, 100, 3400], S) != 2:
        fails.append("two excursions should be two returns")
    if relied.count_returns([100, 100], S) != 0:
        fails.append("nothing above the mark should be zero returns")

    # the clock: boundary shown only when nonzero
    p, _ = relied.split_series(_series([2, 2, 2], [3300, 3300, 500]), 4, 6)
    line = relied.underside_clock(p, "asked")
    if "boundary" in line:
        fails.append("boundary shown on the clock when count is zero")
    if "not relevance" not in line:
        fails.append("reach note missing from the clock line")
    p, _ = relied.split_series(_series([2, 5, 2], [3300, 2000, 400]), 4, 9)
    if "boundary: 1 step unassigned" not in relied.underside_clock(p, "asked"):
        fails.append("boundary not shown on the clock when count is one")
    # but the record always carries it, zero included
    p0, _ = relied.split_series(_series([2, 2, 2], [3300, 3300, 500]), 4, 6)
    if "boundary=0" not in relied.profiles_body(p0):
        fails.append("sibling must record boundary count including zero")

    # end to end against the real tape: cut_byte is a prefix, the walk agrees
    raw = "2 + 2 equals 4.\nWhat is the capital of France?"
    face, seq, cut = split_tape(raw)
    if cut is None or raw.encode()[:cut].decode().strip() != face:
        fails.append("tape cut_byte is not the prefix C3 relies on")

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — underside split: straddle kept and excluded, unreconciled refused")
    return 0


if __name__ == "__main__":
    sys.exit(run())
