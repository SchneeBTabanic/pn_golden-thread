#!/usr/bin/env python3
"""!ask /open !closed /revises /reset /fold a b. No model. No GTPS import."""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import run as runmod  # noqa: E402
import tape  # noqa: E402
import turn_record  # noqa: E402


def run():
    fails = []
    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if "governance" in src and "fold.py" in src:
        fails.append("run.py imported GTPS fold")
    br = src.split("if low == \"/bearings\"", 1)
    if len(br) > 1 and "_run_inquire(" in br[1].split("if low ==", 1)[0]:
        fails.append("/bearings feeds /inquire — that is a chain")
    if "_run_inquire(" not in src:
        fails.append("/inquire walker missing")
    if "parse_ask_line" not in src:
        fails.append("!ask handler missing")

    if tape.parse_ask_line("hello") is not None:
        fails.append("plain talk parsed as !ask")
    if tape.parse_ask_line("!ask") != "":
        fails.append("bare !ask should parse empty question")
    q = tape.parse_ask_line("!ask how should the buffer reach scribe")
    if q != "how should the buffer reach scribe":
        fails.append("!ask lost the question: " + repr(q))
    if tape.parse_closed_line("!closed 1") != "1":
        fails.append("!closed 1 missed")
    if tape.parse_closed_line("hold: x") is not None:
        fails.append("hold parsed as !closed")

    parsed = tape.parse_revises_line("/revises")
    if parsed is None or parsed[2] == "":
        fails.append("bare /revises must name the miss")
    tok, notes, err = tape.parse_revises_line("/revises 3")
    if tok != "3" or notes or err:
        fails.append(" /revises 3 drifted: " + repr((tok, notes, err)))
    tok, notes, err = tape.parse_revises_line(
        '/revises 3 rejected:"assumed fresh" invariant:"still needs disclosure"')
    if err or tok != "3" or notes.get("rejected") != "assumed fresh":
        fails.append("revises notes missed: " + repr((tok, notes, err)))
    tok, notes, err = tape.parse_revises_line("/revises 3 vibe:\"nope\"")
    if not err:
        fails.append("unknown revises key was accepted")

    tmp = tempfile.mkdtemp(prefix="gt-ledger-")
    pile = os.path.join(tmp, "turns.pn")
    old = os.environ.get("GT_TURN_PILE")
    os.environ["GT_TURN_PILE"] = pile
    try:
        turn_record.ensure_session()
        _g, just_clerk = turn_record.load_pile(pile)
        del _g
        if not turn_record.minutes_absent(just_clerk):
            fails.append("fresh pile must be stamp + session-charter only")
        kinds = [k for k, _o, _e in turn_record.clerk_occupants(just_clerk)]
        if kinds != ["stamp", "session-charter"]:
            fails.append("clerk occupants drifted: " + repr(kinds))
        if "minutes_absent" not in src or "/views all" not in src:
            fails.append("run.py /views must name clerk-only and keep /views all")
        t1, g = turn_record.record_turn("one", "a", "bare")
        t2, g = turn_record.record_turn("two", "b", "bare")
        del t1, t2
        name, g = turn_record.record_ask("how should the buffer reach scribe")
        genesis, asks = turn_record.active_asks()
        if len(asks) != 1:
            fails.append("open ask not listed: " + str(len(asks)))
        art, err = turn_record.fold_articulate(1, 2)
        if err or "ALIVE" not in art or "buffer" not in art:
            fails.append("fold articulate lost the ask: " + repr(art[:200]))
        turn_record.record_ask_closed(name, "closed by hand")
        genesis, asks = turn_record.active_asks()
        if asks:
            fails.append("closed ask still open")
        genesis, turns = turn_record.gather_turns(0)
        seat = "2"
        g2, tgt, miss = turn_record.resolve_turn_seat(seat)
        if tgt is None:
            fails.append("seat 2 missed: " + miss)
        else:
            ref = turn_record.traveling_name(g2, tgt)
            turn_record.record_revises_mark(ref, {"rejected": "was thin"})
            t3, g = turn_record.record_turn(
                "three", "c", "bare", extra_tags=[("ref", ref)])
            del t3
            moves = turn_record.inquire_moves(tgt)
            kinds = [k for k, _r in moves]
            if "revises-in" not in kinds:
                fails.append("inquire_moves missed incoming revises: " + repr(moves))
        art, err = turn_record.fold_articulate(1, 3)
        if err or "REVISES" not in art:
            fails.append("fold articulate lost revises")
        if "ONE NEXT" not in art or "quiet" not in art:
            fails.append("closed asks should leave quiet ONE NEXT: " + repr(art[-200:]))
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
    print("PASS — ask/revises/fold-articulate; bearings is not a chain")
    return 0


if __name__ == "__main__":
    sys.exit(run())
