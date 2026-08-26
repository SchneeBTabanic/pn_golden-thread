#!/usr/bin/env python3
"""Bind seat: 2B at :8081 reads /sheet against the face. Speech not score."""
import inspect
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import model  # noqa: E402
import run as runmod  # noqa: E402
import turn_record  # noqa: E402
from pile_io import load_pile  # noqa: E402


def run():
    fails = []
    talk = runmod.Talk()
    talk.last_proposal = ""
    talk.last_bind = ""
    rc = talk.handle("/keep")
    if rc != "loop":
        fails.append("/keep without proposal must loop")

    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if 'print("/keep needs a /sheet proposal first.")' not in src:
        fails.append("/keep without proposal must refuse in stable English")
    if 'print("/bind needs a /sheet proposal first.")' not in src:
        fails.append("/bind without proposal must refuse in stable English")

    tmp = tempfile.mkdtemp(prefix="gt-bind-")
    pile = os.path.join(tmp, "turns.pn")
    old = os.environ.get("GT_TURN_PILE")
    os.environ["GT_TURN_PILE"] = pile
    try:
        turn_record.record_turn("q", "a doing in the harbour", "bare")
        genesis, last = turn_record.last_turn()
        ref_id = turn_record.traveling_name(genesis, last)
        talk.last_proposal = "@act:hear-the-net-lying\n@path:away-from-the-hero-template\n"
        talk.last_bind = ""
        rc = talk.handle("/keep")
        if rc != "loop":
            fails.append("/keep with empty last_bind must still loop")
        _g, blocks = load_pile(pile)
        sheets = [b for b in blocks if turn_record.tag_first(b, "topic") == "sheet"]
        binds = [b for b in blocks if turn_record.tag_first(b, "topic") == "bind"]
        if len(sheets) != 1:
            fails.append("keep without bind should still file the sheet block")
        if len(binds) != 1:
            fails.append("keep without bind must record named absence")
        else:
            if runmod.BIND_ABSENT not in binds[0]["body"]:
                fails.append("absence line missing from bind block")
            if turn_record.tag_first(binds[0], "act"):
                fails.append("bind block must not carry @act")
            if turn_record.tag_first(binds[0], "path"):
                fails.append("bind block must not carry @path")
        talk.last_proposal = ""
        talk.last_bind = ""
        rc = talk.handle("/bind")
        if rc != "loop":
            fails.append("/bind without proposal must loop")
        # second keep after bind-missing should have used the first proposal;
        # /bind now should still refuse.
    finally:
        if old is None:
            os.environ.pop("GT_TURN_PILE", None)
        else:
            os.environ["GT_TURN_PILE"] = old

    look_src = inspect.getsource(model.look)
    bind_src = inspect.getsource(model.bind)
    sheet_src = inspect.getsource(model.sheet)
    walker_src = inspect.getsource(model.walker)
    face_src = inspect.getsource(model.face)
    if "WALK" not in look_src or "walk_up" not in look_src:
        fails.append("leftover look must POST GT_WALK")
    if "return walker(" not in bind_src:
        fails.append("bind must reuse walker HTTP")
    if "WALK" not in sheet_src or "WALK" not in walker_src:
        fails.append("sheet/walker must stay on GT_WALK")
    if "_complete(" not in face_src:
        fails.append("face() must use the face helper")
    if "model.face(INQUIRE_SYSTEM" not in src:
        fails.append("inquire must stay on the face helper")
    if "model.face(BEARINGS_SYSTEM" not in src:
        fails.append("bearings must stay on the face helper")
    if "model.look(INQUIRE_SYSTEM" in src or "model.look(BEARINGS_SYSTEM" in src:
        fails.append("inquire/bearings must not use look() after LOOK moved to WALK")

    if "Do not score" not in runmod.BIND_SYSTEM:
        fails.append("BIND_SYSTEM must contain Do not score")
    if "Do not tell the human to keep" not in runmod.BIND_SYSTEM:
        fails.append("BIND_SYSTEM must contain Do not tell the human to keep")
    if "EXECUTOR" in runmod.BIND_SYSTEM or "WHISTLEBLOWER" in runmod.BIND_SYSTEM:
        fails.append("BIND_SYSTEM must not name Executor/Whistleblower/Proxy")

    rec = inspect.signature(turn_record.record_bind)
    if "accepted" in rec.parameters:
        fails.append("record_bind must not take an accepted tag-list")

    stack = open(os.path.join(HERE, "path_stack.py"), encoding="utf-8").read()
    l2 = stack.split("def granite_l2_tags(", 1)[1].split("def run_gloss(", 1)[0]
    if "model.face(" not in l2:
        fails.append("granite_l2_tags must stay on the face")
    if "model.look(" in l2:
        fails.append("granite_l2_tags must not follow LOOK onto :8081")

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — bind seat: 2B walks the proposal; LOOK on WALK; /keep names absence")
    return 0


if __name__ == "__main__":
    sys.exit(run())
