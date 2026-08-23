#!/usr/bin/env python3
"""Phase 2: hold: in stasis. Banner byte-tested. No model."""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import examine  # noqa: E402
import run as runmod  # noqa: E402
import tape  # noqa: E402
import turn_record  # noqa: E402
from pile_io import load_pile  # noqa: E402


BANNER = (
    "[HELD — testimony placed by the human, in stasis. Not fact, not error.\n"
    "Do not adopt it. Do not argue it away. Answer from yourself.\n"
    "If your answer contradicts it, say so plainly and leave it held.\n"
    "It is released only by the human, never by an answer.]"
)

HOLD_TAGS = (
    ("topic", "held"),
    ("name", "held"),
    ("origin", "human"),
    ("source", "runtime"),
    ("captured", "golden-thread"),
    ("aspect", "prospective"),
    ("part", "held"),
)


def run():
    fails = []
    if turn_record.HOLD_BANNER != BANNER:
        fails.append("HOLD_BANNER drifted from the work-order verbatim")
    if "HELD" not in tape.CLERK_LABELS or "RELEASED" not in tape.CLERK_LABELS:
        fails.append("CLERK_LABELS missing HELD/RELEASED")
    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if "hold: needs testimony. Nothing was held." not in src:
        fails.append("empty-hold refusal string drifted")
    if "nothing is held." not in src:
        fails.append("/held empty string drifted")
    if "/release needs a hold ref and a reason." not in src:
        fails.append("release missing-reason string drifted")
    if "/release: not a held block, or the ref missed." not in src:
        fails.append("release miss-ref string drifted")
    if "/release: already released." not in src:
        fails.append("already-released string drifted")
    if examine.held_clock(0) != "HELD: none":
        fails.append("held clock none drifted: " + repr(examine.held_clock(0)))
    if examine.held_clock(1) != "HELD: 1 in stasis":
        fails.append("held clock n drifted: " + repr(examine.held_clock(1)))

    got = tape.parse_hold_line("hold:")
    if got is None or got[0] != "":
        fails.append("empty hold: must parse as empty testimony")
    got = tape.parse_hold_line("hello")
    if got is not None:
        fails.append("plain talk was parsed as hold")
    got = tape.parse_hold_line(
        "hold: I count 2. !awaits until he releases !dissolves when he says")
    if got is None:
        fails.append("hold with bangs did not parse")
    else:
        tes, aw, ds = got
        if "count 2" not in tes:
            fails.append("testimony lost: " + repr(tes))
        if "until" not in aw:
            fails.append("awaits lost: " + repr(aw))
        if "when" not in ds:
            fails.append("dissolves lost: " + repr(ds))

    tmp = tempfile.mkdtemp(prefix="gt-hold-")
    pile = os.path.join(tmp, "turns.pn")
    old = os.environ.get("GT_TURN_PILE")
    os.environ["GT_TURN_PILE"] = pile
    try:
        token, gen = turn_record.record_hold(
            "I count 2.", awaits="until he releases",
            dissolves="when he says")
        if not token.startswith("辻") or "/" not in token:
            fails.append("hold mint not three-part")
        genesis, holds = turn_record.active_holds()
        if len(holds) != 1:
            fails.append(f"expected 1 active hold, got {len(holds)}")
        else:
            tes = turn_record.field(holds[0]["body"], "HELD")
            if tes != "I count 2.":
                fails.append("HELD body drifted: " + repr(tes))
            if turn_record.tag_first(holds[0], "awaits") != "until-he-releases":
                fails.append("awaits not hyphenated")
            if turn_record.tag_first(holds[0], "dissolves") != "when-he-says":
                fails.append("dissolves not hyphenated")
            for k, v in HOLD_TAGS:
                if turn_record.tag_first(holds[0], k) != v:
                    fails.append(
                        "hold tag %s=%r not %r" % (
                            k, turn_record.tag_first(holds[0], k), v))
        banners, n = runmod._hold_banner_text()
        if n != 1:
            fails.append("banner count without history: " + repr(n))
        if BANNER not in banners or "I count 2." not in banners:
            fails.append("banner missing before any turn")

        bid, _ = turn_record.record_turn("What is 2+2?", "4.", "bare",
                                         hold_refs=[token])
        del bid
        banners, n = runmod._hold_banner_text()
        if n != 1 or BANNER not in banners:
            fails.append("banner missing with history present")
        view = turn_record.view_for_model(4)
        if "I count 2." in view:
            fails.append("held testimony leaked into Executor view")
        if "RELEASED:" in view or "HELD:" in view:
            fails.append("/history showed held/release as turns")
        _, last = turn_record.last_turn()
        if token not in turn_record.tag_values(last, "ref"):
            fails.append("turn under hold missing ref to the hold")
        found = None
        for b in load_pile(pile)[1]:
            if turn_record.traveling_name(genesis, b) == token:
                found = b
                break
        if found is None:
            fails.append("hold ref is not backlinks-resolvable")

        # offset miss, formed-token hit
        formed = token.rsplit("/", 1)[-1]
        _, by_formed, note = turn_record.resolve_hold_ref(
            "辻" + genesis + "#999999/" + formed)
        if by_formed is None:
            fails.append("formed-token resolver missed after offset miss")
        elif "offset missed" not in note:
            fails.append("offset-miss formed-hit was not disclosed")
        _, miss, _ = turn_record.resolve_hold_ref("#999999")
        if miss is not None:
            fails.append("bogus offset resolved as a hold")

        turn_record.record_forget(1)
        genesis, holds = turn_record.active_holds()
        if len(holds) != 1:
            fails.append("hold did not survive /forget")
        banners, n = runmod._hold_banner_text()
        if n != 1 or BANNER not in banners:
            fails.append("banner missing after /forget")

        turn_record.record_release(token, "the count is done")
        genesis, holds = turn_record.active_holds()
        if holds:
            fails.append("release left a hold active")
        banners, n = runmod._hold_banner_text()
        if n != 0 or banners:
            fails.append("banner still present after release")
        _, blocks = load_pile(pile)
        helds = [b for b in blocks if turn_record.tag_first(b, "topic") == "held"]
        if helds and "I count 2." not in helds[0]["body"]:
            fails.append("release edited the held block")
        releases = [
            b for b in blocks if turn_record.tag_first(b, "topic") == "release"]
        if not releases:
            fails.append("release block missing")
        else:
            if turn_record.field(releases[0]["body"], "RELEASED") != (
                    "the count is done"):
                fails.append("RELEASED body drifted")
            if token not in turn_record.tag_values(releases[0], "ref"):
                fails.append("release missing ref to hold")
            if turn_record.tag_first(releases[0], "verified") != (
                    "the-count-is-done"):
                fails.append("release verified not hyphenated reason")
            if turn_record.tag_first(releases[0], "name") != "release":
                fails.append("release name tag drifted")
        view = turn_record.view_for_model(4)
        if "the count is done" in view:
            fails.append("release block leaked into /history")

        # already released: formed still finds the held block, not active
        _, held_again, _ = turn_record.resolve_hold_ref(token)
        if held_again is None:
            fails.append("released hold became unresolvable")
        _, still_active = turn_record.active_holds()
        if still_active:
            fails.append("released hold still active")
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
    print("PASS — hold: stasis; banner verbatim; forget-safe; release appends")
    return 0


if __name__ == "__main__":
    sys.exit(run())
