#!/usr/bin/env python3
"""scribe export is the joiner. The model is not."""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import pile_io  # noqa: E402
import turn_record  # noqa: E402


def run():
    fails = []
    tmp = tempfile.mkdtemp(prefix="gt-export-")
    pile = os.path.join(tmp, "turns.txt")
    old = os.environ.get("GT_TURN_PILE")
    os.environ["GT_TURN_PILE"] = pile
    try:
        turn_record.record_turn("q1", "a1", "bare")
        turn_record.record_turn("q2", "a2", "file", fetched="/tmp/x")
        slab = pile_io.export_selector(pile, "topic:turn")
        if "ASKED:" not in slab or "q1" not in slab or "q2" not in slab:
            fails.append("export topic:turn lost bodies")
        try:
            pile_io.export_selector(pile, "not-a-selector")
            fails.append("export accepted a bare word")
        except pile_io.PileError:
            pass
        try:
            pile_io.export_selector(pile, "act:does-not-exist-here")
            fails.append("empty export should refuse")
        except pile_io.PileError:
            pass
    except Exception as e:
        fails.append(f"exception: {e}")
    finally:
        if old is None:
            os.environ.pop("GT_TURN_PILE", None)
        else:
            os.environ["GT_TURN_PILE"] = old
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — scribe export joins a named gather")
    return 0


if __name__ == "__main__":
    sys.exit(run())
