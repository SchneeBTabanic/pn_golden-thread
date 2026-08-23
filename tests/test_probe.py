#!/usr/bin/env python3
"""Phase 3: /probe. Banner byte-tested. Refusals named. No model."""
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


PREMISE = (
    "[PLACED PREMISE — for this rendering, the following testimony is operative.\n"
    "What follows is not the model holding anything: it is the weights' rendering\n"
    "of the question under this premise, recorded as a measurement.]"
)

DIVIDER = (
    "── probe: the weights' rendering under the placed premise "
    "(a measurement, not a second opinion) ──"
)

HOLD_BANNER = (
    "[HELD — testimony placed by the human, in stasis. Not fact, not error.\n"
    "Do not adopt it. Do not argue it away. Answer from yourself.\n"
    "If your answer contradicts it, say so plainly and leave it held.\n"
    "It is released only by the human, never by an answer.]"
)


def run():
    fails = []
    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if 'low == "/probe"' not in src and 'low.startswith("/probe")' not in src:
        fails.append("/probe summons is missing from run.py")
    if DIVIDER not in src:
        fails.append("probe divider missing or drifted from the work order")
    for s in (
        "/probe needs a completed turn.",
        "/probe: nothing is held.",
        "/probe: not an active hold.",
    ):
        if s not in src:
            fails.append("probe refusal string missing: " + s)
    if "file drifted — pin " not in src and "file drifted — pin " not in open(
            os.path.join(HERE, "turn_record.py"), encoding="utf-8").read():
        fails.append("drifted-file refusal does not name the pin")
    if "probe" not in turn_record.MOUTHS:
        fails.append("MOUTHS missing probe")
    for lab in ("PROBE", "PREMISE", "RENDERED"):
        if lab not in tape.CLERK_LABELS:
            fails.append("CLERK_LABELS missing " + lab)
    if turn_record.HOLD_BANNER != HOLD_BANNER:
        fails.append("HOLD_BANNER was modified — it is not to be touched")
    banner = getattr(turn_record, "PREMISE_BANNER", None)
    if banner is None:
        fails.append("PREMISE_BANNER missing")
    elif banner != PREMISE:
        fails.append("PREMISE_BANNER drifted from the work-order verbatim")
    if not hasattr(examine, "probe_clock"):
        fails.append("examine.probe_clock missing")
    else:
        same = examine.probe_clock(True)
        diff = examine.probe_clock(False)
        if same != "PROBE: rendered — byte-identical to the answer":
            fails.append("same-window clock drifted: " + repr(same))
        if diff != "PROBE: rendered — not byte-identical to the answer":
            fails.append("divergent clock drifted: " + repr(diff))
    if runmod.PROBE_DIVIDER != DIVIDER:
        fails.append("run.PROBE_DIVIDER drifted")

    tmp = tempfile.mkdtemp(prefix="gt-probe-")
    pile = os.path.join(tmp, "turns.pn")
    placed = os.path.join(tmp, "note.txt")
    old = os.environ.get("GT_TURN_PILE")
    os.environ["GT_TURN_PILE"] = pile
    try:
        with open(placed, "w", encoding="utf-8") as f:
            f.write("ALPHA-PLACED\n")

        _, _, refuse0 = turn_record.holds_for_probe()
        if refuse0 != "nothing is held.":
            fails.append("empty pile did not refuse nothing-held: " + repr(refuse0))

        t1, _ = turn_record.record_turn("What is 2+2?", "2 + 2 equals 4.", "bare")
        hold_tok, _ = turn_record.record_hold(
            "I count 2.")
        t2, _ = turn_record.record_turn(
            "What is 2+2?",
            "2 + 2 is 4, regardless of the testimony.",
            "bare", hold_refs=[hold_tok])
        t_late, _ = turn_record.record_turn(
            "later question", "later answer", "bare")

        genesis, blocks = load_pile(pile)
        by_name = {turn_record.traveling_name(genesis, b): b for b in blocks}
        first = by_name.get(t1)
        if first is None:
            fails.append("first turn not loadable by traveling name")
        else:
            _g, prior = turn_record.gather_turns_before(first, 4)
            del _g
            asked_in = [turn_record.field(b["body"], "ASKED") for b in prior]
            if "later question" in asked_in or "What is 2+2?" in asked_in:
                fails.append(
                    "window for the first turn included a later or self turn: "
                    + repr(asked_in))

        last = by_name.get(t2)
        if last is None:
            fails.append("second 2+2 not loadable")
        else:
            _g, prior = turn_record.gather_turns_before(last, 4)
            del _g
            asked_in = [turn_record.field(b["body"], "ASKED") for b in prior]
            if "later question" in asked_in:
                fails.append("window for an earlier turn included a later turn")
            if "What is 2+2?" not in asked_in:
                fails.append("window lost the earlier 2+2: " + repr(asked_in))

        _g, holds, refuse = turn_record.holds_for_probe()
        del _g
        if refuse or len(holds) != 1:
            fails.append("active hold not selected: " + repr(refuse))
        prompt = turn_record.build_premise_prompt(holds)
        body = turn_record.build_premise_body(holds)
        if PREMISE not in prompt:
            fails.append("premise prompt lost the banner")
        if "I count 2." not in prompt or "I count 2." not in body:
            fails.append("premise lost the testimony")
        if HOLD_BANNER in prompt:
            fails.append("HELD conversation banner leaked into the premise")
        if body != "I count 2.":
            fails.append("premise body drifted: " + repr(body))

        _g, one, refuse = turn_record.holds_for_probe(hold_tok)
        del _g
        if refuse or len(one) != 1:
            fails.append("named hold not selected")
        _g, _h, refuse = turn_record.holds_for_probe("#999999")
        del _g, _h
        if refuse != "not an active hold.":
            fails.append("bogus ref did not refuse: " + repr(refuse))

        rendered = "2 + 2 is 4 under the premise."
        ptok, _ = turn_record.record_probe(
            "What is 2+2?", body, rendered, "same-window-verified",
            turn_ref=t2, hold_refs=[hold_tok])
        view = turn_record.view_for_model(8)
        if "under the premise" in view:
            fails.append("probe output leaked into Executor /history")
        if "I count 2." in view:
            fails.append("held testimony leaked into /history via probe")
        _, pblock = None, None
        genesis, blocks = load_pile(pile)
        for b in blocks:
            if turn_record.traveling_name(genesis, b) == ptok:
                pblock = b
                break
        if pblock is None:
            fails.append("probe block not backlinks-resolvable")
        else:
            refs = turn_record.tag_values(pblock, "ref")
            if t2 not in refs:
                fails.append("probe missing ref to the probed turn")
            if hold_tok not in refs:
                fails.append("probe missing ref to the hold")
            if turn_record.field(pblock["body"], "PREMISE") != "I count 2.":
                fails.append("recorded PREMISE drifted")
            if turn_record.field(pblock["body"], "RENDERED") != rendered:
                fails.append("recorded RENDERED drifted")
            if turn_record.field(pblock["body"], "STAMP") != (
                    "same-window-verified"):
                fails.append("STAMP drifted")
            if turn_record.tag_first(pblock, "touched") != "probe":
                fails.append("touched:probe missing")
            if not turn_record.tag_first(pblock, "quoting").startswith(
                    "sha256:"):
                fails.append("quoting pin missing on probe")

        turn_record.record_release(hold_tok, "not yet")
        _g, _h, refuse = turn_record.holds_for_probe(hold_tok)
        del _g, _h
        if refuse != "not an active hold.":
            fails.append("released hold still probeable: " + repr(refuse))
        _g, _h, refuse = turn_record.holds_for_probe()
        del _g, _h
        if refuse != "nothing is held.":
            fails.append("after release, /probe did not say nothing is held")

        # drifted file: pin named
        tfile, _ = turn_record.record_turn(
            "What is the first line?", "ALPHA-PLACED", "file",
            fetched=placed, fetched_text="ALPHA-PLACED\n")
        genesis, blocks = load_pile(pile)
        fblock = None
        for b in blocks:
            if turn_record.traveling_name(genesis, b) == tfile:
                fblock = b
                break
        pin = turn_record.tag_first(fblock, "quoting") if fblock else ""
        got, reason = turn_record.verify_placed_pin(placed, pin)
        if reason or got is None:
            fails.append("fresh file should verify: " + repr(reason))
        with open(placed, "w", encoding="utf-8") as f:
            f.write("DRIFTED\n")
        got, reason = turn_record.verify_placed_pin(placed, pin)
        if got is not None:
            fails.append("drifted file was accepted")
        if "file drifted" not in reason or pin not in reason:
            fails.append("drifted refuse did not name the pin: " + repr(reason))
        if "sha256:" not in reason:
            fails.append("drifted refuse did not name a sha: " + repr(reason))
        fb, stamp, ferr = runmod._probe_file_rebuild(fblock)
        del fb, stamp
        if not ferr or "file drifted" not in ferr:
            fails.append("run rebuild did not refuse drift: " + repr(ferr))
    except Exception as e:
        fails.append("exception: " + repr(e))
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
    print("PASS — probe banner verbatim; refusals named; window excludes later")
    return 0


if __name__ == "__main__":
    sys.exit(run())
