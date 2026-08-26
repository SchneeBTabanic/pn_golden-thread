#!/usr/bin/env python3
"""Beneath sheet: meanings not a menu; /keep copies; clerk invents nothing."""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import path_stack  # noqa: E402
import pile_io  # noqa: E402
import turn_record  # noqa: E402


def run():
    fails = []
    acc, ref = path_stack.parse_proposal(
        "noise\n"
        "@act:carry-the-bucket\n"
        "@path:toward-the-open-gate\n"
        "@rejected:counting-as-arithmetic\n"
        "@mystery:on-the-fly\n"
        "@origin:ai\n"
        "@kept:nope\n"
        "@awaits:the first citation\n"
    )
    keys = [k for k, _ in acc]
    if "act" not in keys or "path" not in keys:
        fails.append("lost act/path: " + str(acc))
    if ("rejected", "counting-as-arithmetic") not in acc:
        fails.append("lost witness key")
    if ("mystery", "on-the-fly") not in acc:
        fails.append("invented witness key must be allowed: " + str(acc))
    if not any("writer-owned origin" in r for r in ref):
        fails.append("origin must stay writer-owned: " + str(ref))
    if not any("closed-class kept" in r for r in ref):
        fails.append("bad @kept must refuse: " + str(ref))
    if not any(r.startswith("space ") for r in ref):
        fails.append("space in value must refuse: " + str(ref))

    tmp = tempfile.mkdtemp(prefix="gt-sheet-")
    pile = os.path.join(tmp, "turns.pn")
    old = os.environ.get("GT_TURN_PILE")
    os.environ["GT_TURN_PILE"] = pile
    try:
        turn_record.record_turn(
            asked="I carried the bucket.", answered="A task with water.",
            kind="bare")
        genesis, last = turn_record.last_turn()
        ref_id = turn_record.traveling_name(genesis, last)
        speech = "@act:carry-the-bucket\n@path:toward-the-open-gate\n"
        acc2, ref2 = path_stack.parse_proposal(speech)
        turn_record.record_sheet(speech, acc2, ref2, ref_id=ref_id)
        _gen, blocks = pile_io.load_pile(pile)
        sheets = [b for b in blocks if turn_record.tag_first(b, "topic") == "sheet"]
        if len(sheets) != 1:
            fails.append("expected 1 sheet block, got " + str(len(sheets)))
        else:
            if turn_record.tag_first(sheets[0], "act") != "carry-the-bucket":
                fails.append("kept @act did not land")
            if turn_record.tag_first(sheets[0], "path") != "toward-the-open-gate":
                fails.append("kept @path did not land")
            if turn_record.tag_first(last, "act"):
                fails.append("the turn must stay empty until a later gather")
    finally:
        if old is None:
            os.environ.pop("GT_TURN_PILE", None)
        else:
            os.environ["GT_TURN_PILE"] = old

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — sheet proposal parse; /keep copies; turn stays empty")
    return 0


if __name__ == "__main__":
    sys.exit(run())
