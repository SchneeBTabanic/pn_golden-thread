#!/usr/bin/env python3
"""Phase 1: gForth keep is the writer; Python reads by extent."""
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
    tmp = tempfile.mkdtemp(prefix="gt-gf-")
    pile = os.path.join(tmp, "turns.pn")
    old = os.environ.get("GT_TURN_PILE")
    os.environ["GT_TURN_PILE"] = pile
    try:
        token, gen = turn_record.record_turn("q", "a", "bare")
        if not token.startswith("辻") or "/" not in token or "#" not in token:
            fails.append(f"KEPT token not three-part: {token!r}")
        if not gen.startswith("辻"):
            fails.append(f"genesis missing: {gen!r}")
        genesis, blocks = pile_io.load_pile(pile)
        if genesis != gen:
            fails.append("load_pile genesis mismatch")
        if not blocks:
            fails.append("no blocks")
        else:
            stamp = blocks[0]
            if pile_io.tag_map(stamp["tags"]).get("genesis") != gen:
                fails.append("stamp block does not carry @genesis:")
            if "id" in stamp["tagmap"] or stamp["header"].startswith("@@ #"):
                fails.append("python-scribe header leaked into a gForth pile")
        slab = pile_io.export_selector(pile, "topic:turn")
        if "ASKED:" not in slab or "q" not in slab:
            fails.append("export-bare lost the turn body")

        hostile = os.path.join(tmp, 'x" evil s" y.pn')
        os.environ["GT_TURN_PILE"] = hostile
        tok_h, _ = turn_record.record_turn("hostile", "ok", "bare")
        if not os.path.isfile(hostile):
            fails.append("hostile filename was not created as a path")
        if "evil" in tok_h and "s\"" in tok_h:
            fails.append("hostile filename was interpolated into identity")
        _, hblocks = pile_io.load_pile(hostile)
        if len(hblocks) < 2:
            fails.append("hostile pile was not a real keep")

        # over-length tags must REFUSE, not truncate then keep
        os.environ["GT_TURN_PILE"] = pile
        long_val = "x" * 500
        try:
            pile_io.capture_append(
                pile, "body\n",
                [("act", "hold-a-thing"), ("path", "toward-a-named-place"),
                 ("topic", long_val)])
            fails.append("over-length tag string was kept")
        except pile_io.PileError as e:
            if "512" not in str(e) and "longer" not in str(e).lower():
                fails.append(f"wrong refusal for over-length tags: {e}")

        # python-scribe header is a named refusal
        py = os.path.join(tmp, "old.txt")
        with open(py, "w", encoding="utf-8") as f:
            f.write("@@ #12 2026-08-20T00:00:00 @topic:turn\nASKED:\nx\n")
        try:
            pile_io.load_pile(py)
            fails.append("python-scribe header was accepted")
        except pile_io.PileError as e:
            if "python-scribe" not in str(e):
                fails.append(f"wrong refusal for python header: {e}")
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
    print("PASS — gForth keep mints; Python reads by extent; hostile path inert")
    return 0


if __name__ == "__main__":
    sys.exit(run())
