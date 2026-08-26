#!/usr/bin/env python3
"""C2: the per-token series. The hook is cut-ignorant; nothing here knows a cut."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import relied  # noqa: E402


def _resp(bytes_, spans, scale=relied.SERIES_SCALE, prefix=0):
    return {"gt_relied": {"asked": 0.29},
            "gt_relied_series": {"scale": scale, "bytes": bytes_,
                                 "prefix_bytes": prefix, "spans": spans}}


def run():
    fails = []

    # additive: a pre-C2 hook still carries the old fraction field
    old = {"gt_relied": {"asked": 0.29}}
    if relied.parse_gt_relied(old) is None:
        fails.append("old fraction field stopped parsing — C2 is not additive")
    s, note = relied.parse_series(old)
    if s is not None or note != relied.NO_SERIES:
        fails.append("absent series must be a named refusal, not None-and-silence")

    # a good series
    s, note = relied.parse_series(_resp([3, 1, 4], {"asked": [1200, 340, 0]}))
    if s is None:
        fails.append("valid series refused: " + note)
    else:
        if s["bytes"] != [3, 1, 4]:
            fails.append("byte lengths lost")
        if s["spans"]["asked"] != [1200, 340, 0]:
            fails.append("span masses lost")
        if relied.series_total_bytes(s) != 8:
            fails.append("series_total_bytes wrong")

    # ragged is refused, never padded
    s, note = relied.parse_series(_resp([3, 1, 4], {"asked": [1200, 340]}))
    if s is not None or note != relied.SERIES_RAGGED:
        fails.append("ragged series must be refused, not padded")

    # a zero mass is a reading, not an absence
    s, _ = relied.parse_series(_resp([1], {"asked": [0]}))
    if s is None or s["spans"]["asked"] != [0]:
        fails.append("a zero reading was dropped — that is discarding")

    # integers survive the round trip; no float reformatting
    body = relied.series_body(s)
    if "scale=10000" not in body or "steps=1" not in body:
        fails.append("series_body lost its scale or step count")
    if "\n" in body.split("bytes ")[1].split("\n")[0]:
        fails.append("bytes line is not one line")

    # a span id with a space is refused rather than writing a broken line
    bad = {"scale": 10000, "bytes": [1], "spans": {"has space": [0]}}
    try:
        relied.series_body(bad)
        fails.append("span id with a space was written instead of refused")
    except ValueError:
        pass

    # prefix_bytes: the unmeasured first token is counted, never invented as 0
    s, _ = relied.parse_series(_resp([2, 1], {"asked": [10, 20]}, prefix=3))
    if s is None or s["prefix_bytes"] != 3:
        fails.append("prefix_bytes lost — the unmeasured region went silent")
    if not relied.series_accounts_for(s, 6):
        fails.append("prefix + bytes should reconcile with the generation")
    if relied.series_accounts_for(s, 7):
        fails.append("a series that does not account for the generation was accepted")
    if "prefix=3" not in relied.series_body(s):
        fails.append("series_body dropped the prefix")

    # the hook says nothing about cuts
    if "boundary" in body or "cut" in body:
        fails.append("series body mentions a cut — the hook must stay cut-ignorant")

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — per-token series: additive, ragged refused, zero kept, cut-ignorant")
    return 0


if __name__ == "__main__":
    sys.exit(run())
