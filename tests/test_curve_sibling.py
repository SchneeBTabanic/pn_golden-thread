#!/usr/bin/env python3
"""The curve is filed as its OWN block (F3), and a missing curve files nothing.

The refusal this suite exists to protect: a turn with no reading must leave NO
sibling. A block of zeros would be a measured nothing, which is a reading the
instrument never took. Absence is structural.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import relied  # noqa: E402
import turn_record  # noqa: E402
from pile_io import load_pile  # noqa: E402


def _series(bytes_, spans, prefix=0):
    return {"scale": relied.SERIES_SCALE, "bytes": bytes_,
            "prefix_bytes": prefix, "spans": spans}


def _blocks(path):
    if not os.path.exists(path):
        return []
    _, blocks = load_pile(path)
    return blocks


def _curve_blocks(path):
    out = []
    for b in _blocks(path):
        for key, val in b.get("tags") or []:
            if key == "part" and val == "curve":
                out.append(b)
                break
    return out


def run():
    fails = []
    tmp = tempfile.mkdtemp(prefix="gt-curve-")
    pile = os.path.join(tmp, "turns.pn")
    os.environ["GT_TURN_PILE"] = pile

    # ---- 1. NO SERIES, NO SIBLING. The whole point of the suite. -----------
    bid, gen = turn_record.record_curve("turn-1", None)
    if (bid, gen) != (None, None):
        fails.append("a turn with no series must file no curve block")
    if _curve_blocks(pile):
        fails.append("a curve block was written for a turn that had no reading")
    for empty in ({}, {"bytes": []}):
        if turn_record.record_curve("turn-1", empty)[0] is not None:
            fails.append("an empty series must file no curve block")

    # ---- 2. a real series with profiles files ONE sibling ------------------
    ser = _series([3, 1, 4], {"asked": [3300, 0, 500]}, prefix=2)
    profiles, note = relied.split_series(ser, 4, 10)
    if profiles is None:
        fails.append("split refused a reconciling series: " + str(note))
    else:
        bid, gen = turn_record.record_curve("turn-2", ser, profiles)
        if not bid:
            fails.append("a real curve was not filed")
        curves = _curve_blocks(pile)
        if len(curves) != 1:
            fails.append("expected exactly one curve block, got %d" % len(curves))
        else:
            b = curves[0]
            body = b.get("body") or ""
            tags = b.get("tags") or []
            if "SERIES " not in body:
                fails.append("curve block carries no SERIES section")
            if "PROFILES " not in body:
                fails.append("curve block carries no PROFILES section")
            if "3300 0 500" not in body:
                fails.append("integers did not survive to the pile verbatim")
            if "boundary=" not in body:
                fails.append("boundary count must be recorded, zero included")
            if ("ref", "turn-2") not in tags:
                fails.append("curve block does not @ref: the turn it annotates")
            if not any(k == "binned" for k, _ in tags):
                fails.append("header carries no binned disclosure")
            if any(k == "act" for k, _ in tags) or any(k == "path" for k, _ in tags):
                fails.append("a curve is not a way; it must not carry @act:/@path:")
            for key, val in tags:
                if " " in key or " " in val:
                    fails.append("tag with a space would break the header: " + val)

    # ---- 3. a REFUSED split still files its series, and names the refusal ---
    ser2 = _series([3, 1, 4], {"asked": [100, 200, 300]})
    profiles2, note2 = relied.split_series(ser2, 999, 10)
    if profiles2 is not None:
        fails.append("a series that does not reconcile must refuse to split")
    bid, gen = turn_record.record_curve("turn-3", ser2, profiles2, note=note2)
    if not bid:
        fails.append("a refused split must still file the series it did measure")
    curves = _curve_blocks(pile)
    if len(curves) == 2:
        b = curves[1]
        body = b.get("body") or ""
        tags = b.get("tags") or []
        if "SERIES " not in body:
            fails.append("refused-split sibling dropped the reading it did take")
        if "PROFILES " in body:
            fails.append("refused split must not emit a PROFILES section")
        if not any(k == "refuses" for k, _ in tags):
            fails.append("a refused split must be named in the header")
        if "100 200 300" not in body:
            fails.append("refused split discarded the measured masses")
    else:
        fails.append("expected two curve blocks after the refused split")

    # ---- 4. bins are named, never invented for an absence ------------------
    if relied.bin_frac(None) != "none":
        fails.append("an absent mean must bin as none, not as a number")
    if relied.bin_frac(relied.STRONG_MARK) != "strong":
        fails.append("the strong mark must bin as strong")
    if relied.bin_frac(relied.HUM_MARK) != "hum":
        fails.append("the hum mark must bin as hum")
    if relied.curve_bins(None) != []:
        fails.append("no profiles must yield no bins")

    # ---- 4a. A CURVE IS NOT A WAY. keep echo compares @path:/@act:.
    # Costume seats on the sibling made Hello (and any first unique
    # question) announce YOU HAVE REACHED THIS WAY BEFORE against the
    # session charter's hold-the-session-refusals. Not memory of talk.
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        turn_record.ensure_session()
        ser_echo = _series([2, 2], {"asked": [100, 200]})
        prof_echo, _n = relied.split_series(ser_echo, 2, 4)
        turn_record.record_curve("turn-echo", ser_echo, prof_echo)
    notes = buf.getvalue()
    if "YOU HAVE REACHED THIS WAY BEFORE" in notes:
        fails.append("curve keep echoed against clerk: " + notes[:400])

    # ---- 4b. A CURVE IS NOT A TURN. Found by his E2 sitting, 2026-08-24. ---
    # /history rendered every curve as a turn with an empty ASKED and ANSWERED,
    # and counted them in "12 earlier turns not included". Two halves are
    # asserted: the writer no longer tags a curve topic:turn, and the reader
    # excludes one even when it IS -- because piles are append-only and the
    # mis-tagged blocks in his E2 pile cannot be rewritten.
    from pile_io import load_pile  # noqa: F811
    _, blocks = load_pile(pile)
    for b in blocks:
        if turn_record.tag_first(b, "part") == "curve":
            if turn_record.tag_first(b, "topic") == "turn":
                fails.append("a curve is being written as topic:turn again")
            if turn_record.is_turn(b):
                fails.append("a curve block is gathered as a turn")
    legacy = {"tags": [("topic", "turn"), ("part", "curve")], "body": ""}
    if turn_record.is_turn(legacy):
        fails.append("a pile written before the fix still reads a curve "
                     "as a turn -- append-only means the reader must cope")
    plain = {"tags": [("topic", "turn"), ("part", "unmasked")], "body": ""}
    if not turn_record.is_turn(plain):
        fails.append("the fix swallowed a real turn")

    # ---- 5. the sibling never decides anything -----------------------------
    src = open(os.path.join(HERE, "turn_record.py"), encoding="utf-8").read()
    start = src.find("def record_curve(")
    end = src.find("\ndef ", start + 1)
    fn = src[start:end]
    # CODE only. The first version scanned the docstring and comments too, and
    # tripped on the word "selectors" in a comment explaining a bug fix -- the
    # guard firing on prose that DESCRIBES judgement rather than on judgement.
    code = []
    in_doc = False
    for line in fn.splitlines():
        bare = line.strip()
        if bare.startswith('"""'):
            in_doc = not (bare.endswith('"""') and len(bare) > 3) and not in_doc
            continue
        if in_doc or bare.startswith("#"):
            continue
        code.append(line.split("  #")[0])
    code = "\n".join(code)
    for word in ("if mean", "> STRONG", "sorted(", "filter("):
        if word in code:
            fails.append("record_curve appears to judge a curve: " + word)

    os.environ.pop("GT_TURN_PILE", None)
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — curve sibling: no reading files no block, refused split keeps "
          "its series, bins named")
    return 0


if __name__ == "__main__":
    sys.exit(run())
