#!/usr/bin/env python3
"""Turn pile: mouth tags, sheet keys from asserted facts, forget is a cut."""
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
    tmp = tempfile.mkdtemp(prefix="gt-turns-")
    pile = os.path.join(tmp, "turns.txt")
    old = os.environ.get("GT_TURN_PILE")
    os.environ["GT_TURN_PILE"] = pile
    try:
        try:
            turn_record.mouth_tags("weather")
            fails.append("unknown mouth was accepted")
        except pile_io.PileError:
            pass

        bid1, gen = turn_record.record_turn(
            asked="What is 2+2?", answered="4.", kind="bare")
        if not bid1:
            fails.append("capture did not return a block id")
        if not gen.startswith("辻"):
            fails.append(f"new pile was not stamped (genesis={gen!r})")

        bid2, gen2 = turn_record.record_turn(
            asked="Read the charter", answered="§3.3 says…",
            kind="file", fetched="/tmp/x", fetched_text="hello",
            extra_tags=[("act", "place-the-named-file"),
                        ("path", "toward-the-charter")])
        if gen2 != gen:
            fails.append("genesis moved after the second turn")

        genesis, blocks = pile_io.load_pile(pile)
        if genesis != gen:
            fails.append("load_pile genesis mismatch")
        sessions = [b for b in blocks if turn_record.tag_first(b, "topic") == "session"]
        turns = [b for b in blocks if turn_record.tag_first(b, "topic") == "turn"]
        if len(sessions) != 1:
            fails.append(f"expected 1 session charter, got {len(sessions)}")
        if len(turns) != 2:
            fails.append(f"expected 2 turns, got {len(turns)}")
        if turn_record.tag_first(turns[0], "act"):
            fails.append(
                "bare turn must not wear a clerk @act: "
                + turn_record.tag_first(turns[0], "act"))
        if turn_record.tag_first(turns[0], "path"):
            fails.append(
                "bare turn must not wear a clerk @path: "
                + turn_record.tag_first(turns[0], "path"))
        if turn_record.tag_first(turns[0], "aspect"):
            fails.append("clerk must not stamp @aspect")
        if "clause-injection" in turn_record.tag_values(turns[0], "refuses"):
            fails.append("turn still wears clause-vocabulary")
        if turn_record.tag_first(turns[0], "name") != "turn":
            fails.append("turns should be say-again name:turn")
        if "MOUTH: file" not in turns[1]["body"]:
            fails.append("file turn lost MOUTH: file in the minutes")
        if turn_record.tag_first(turns[1], "act") != "place-the-named-file":
            fails.append(
                "generated extra @act should land: "
                + turn_record.tag_first(turns[1], "act"))
        if turn_record.tag_first(turns[1], "path") != "toward-the-charter":
            fails.append("generated extra @path should land")
        import hashlib
        want_sha = "sha256:" + hashlib.sha256(b"hello").hexdigest()[:8]
        if want_sha not in turn_record.tag_values(turns[1], "quoting"):
            fails.append(
                "placed file should pin sha256 of content, not of the path: "
                + str(turn_record.tag_values(turns[1], "quoting")))
        path_sha = "sha256:" + hashlib.sha256(b"/tmp/x").hexdigest()[:8]
        if path_sha in turn_record.tag_values(turns[1], "quoting"):
            fails.append("quoting hashed the path as if it were the file")
        if "because" in [k for k, _ in turns[0]["tags"]]:
            fails.append("runtime inferred @because from the answer")
        if "attests" in [k for k, _ in turns[0]["tags"]]:
            fails.append("runtime wrote @attests — that seat is his")
        if turn_record.tag_first(sessions[0], "gates") != "section-six-comparison":
            fails.append("session charter missing @gates")
        if "cosine-clause-selection" not in turn_record.tag_values(sessions[0], "rejected"):
            fails.append("session charter missing @rejected:cosine")

        view = turn_record.view_for_model(4)
        if "DERIVED VIEW" not in view:
            fails.append("view did not declare itself")
        if bid1 not in view:
            fails.append("traveling name of turn 1 missing from view")
        if "/" not in bid1 or not bid1.startswith("辻"):
            fails.append(f"mint did not return three-part name: {bid1!r}")
        if "What is 2+2?" not in view or "4." not in view:
            fails.append("view lost asked/answered")

        turn_record.record_forget(2)
        _, window = turn_record.gather_turns(4)
        if window:
            fails.append("/forget left turns in the model window")
        g_last, last = turn_record.last_turn()
        if last is None:
            fails.append("last_turn should still find the last Executor turn")
        elif turn_record.traveling_name(g_last, last) != bid2:
            fails.append(
                "last_turn should still find the last Executor turn: "
                + repr(turn_record.traveling_name(g_last, last)))
        genesis3, blocks3 = pile_io.load_pile(pile)
        if genesis3 != gen:
            fails.append("forget rewrote genesis")
        # stamp + session + 2 turns + forget (gForth stamp is an ordinary first block)
        if len(blocks3) < 5:
            fails.append(f"forget should append, not delete; got {len(blocks3)}")

        turn_record.record_shape("none of the scars.", ref_id=bid2)
        _, blocks4 = pile_io.load_pile(pile)
        shapes = [b for b in blocks4 if turn_record.tag_first(b, "topic") == "shape"]
        if len(shapes) != 1:
            fails.append("shape block missing")
        if "none of the scars." not in shapes[0]["body"]:
            fails.append("shape body lost")
        if turn_record.tag_first(shapes[0], "act"):
            fails.append("shape must not wear a clerk @act")
        view2 = turn_record.view_for_model(4)
        if "none of the scars." in view2:
            fails.append("shape speech leaked into the Executor view")

        turn_record.record_comment(
            "this record is for noticing the law being made machine-shaped.",
            ref_id=bid2)
        viewc = turn_record.view_for_model(4)
        if "machine-shaped" in viewc:
            fails.append("comment leaked into the Executor view")
        _, blocks_c = pile_io.load_pile(pile)
        comments = [b for b in blocks_c
                    if turn_record.tag_first(b, "topic") == "comment"]
        if len(comments) != 1:
            fails.append("comment block missing")
        if turn_record.tag_first(comments[0], "act"):
            fails.append("comment must not wear a clerk @act")
        if turn_record.tag_first(comments[0], "path"):
            fails.append("comment must not wear a clerk @path")

        turn_record.record_file_refused("/no/such", "does not exist")
        _, blocks5 = pile_io.load_pile(pile)
        refused = [b for b in blocks5
                   if "MOUTH: refuse-file" in (b.get("body") or "")]
        if len(refused) != 1:
            fails.append("file refusal was not enacted in the pile")

        leaked = (
            "Yes, Steiner founded Anthroposophy.\n"
            "\n"
            "MOUTH: bare\n"
            "FETCHED: (nothing)\n"
            "\n"
            "What is the capital of Brazil?\n"
            "The capital of Brazil is Brasília.\n"
        )
        if turn_record.field(leaked, "ANSWERED"):
            fails.append("field() should not find ANSWERED in a raw leak")
        body = (
            "ASKED:\nWho is Steiner?\n\n"
            "ANSWERED:\nYes, Steiner founded Anthroposophy.\n\n"
            "MOUTH: bare\n"
            "FETCHED: (nothing)\n"
            "What is the capital of Brazil?\n"
        )
        got = turn_record.field(body, "ANSWERED")
        if "Brazil" in got or "MOUTH" in got:
            fails.append(f"field leaked the quiz into ANSWERED: {got!r}")
        if "Steiner founded" not in got:
            fails.append(f"field lost the face: {got!r}")

        bid_s, _ = turn_record.record_sequel(
            "What is the capital of Brazil?\nBrasília.",
            ref_id=bid2)
        if not bid_s:
            fails.append("sequel was not recorded")
        _, blocks_s = pile_io.load_pile(pile)
        sequels = [b for b in blocks_s
                   if turn_record.tag_first(b, "topic") == "sequel"]
        if sequels and turn_record.tag_first(sequels[0], "part") in (
                "on-path", "off-path"):
            fails.append("sequel must not wear clerk on-path/off-path")
        view3 = turn_record.view_for_model(4)
        if "Brasília" in view3:
            fails.append("sequel leaked into the Executor view")

        bid_l, _ = turn_record.record_look(
            "the leftover still sits on the declared path.",
            ref_id=bid2, engine="granite", declared_path="venv")
        if not bid_l:
            fails.append("look was not recorded")
        if turn_record.tag_first(
                [b for b in pile_io.load_pile(pile)[1]
                 if turn_record.tag_first(b, "topic") == "look"][0],
                "act"):
            fails.append("look must not wear a clerk @act")
        view_l = turn_record.view_for_model(4)
        if "leftover still sits" in view_l:
            fails.append("look leaked into the Executor view")
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
    print("PASS — minutes only; clerk does not choose tag values")
    return 0


if __name__ == "__main__":
    sys.exit(run())
