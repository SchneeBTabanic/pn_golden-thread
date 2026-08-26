#!/usr/bin/env python3
"""STOP DISCLOSURE, and the span that used to vanish.

Ruled 2026-08-24 after the stance-check. Two guards, and the second is the one
that matters: a clock that goes SILENT when it cannot tell you is
indistinguishable from a check that never ran. Every path must SAY something.
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import relied  # noqa: E402


def run():
    fails = []

    # ---- 1. the three cases are told apart --------------------------------
    eos = relied.stopped_clock({"stop_type": "eos", "tokens_predicted": 9})
    cap = relied.stopped_clock({"stop_type": "limit", "tokens_predicted": 512})
    wrd = relied.stopped_clock({"stop_type": "word", "stopping_word": "ANSWER_END",
                                "tokens_predicted": 40})
    if not ("eos" in eos and "9" in eos):
        fails.append("eos case does not name eos and the token")
    if "cap" not in cap or "512" not in cap:
        fails.append("cap case does not name the cap and the token")
    if "ANSWER_END" not in wrd:
        fails.append("stop-string case does not name the string")
    if len({eos, cap, wrd}) != 3:
        fails.append("the three endings are not distinguishable — the whole point")

    # ---- 2. NOTHING GOES QUIET. Every degraded input still says something. --
    for label, resp in (
            ("no stop_type", {"tokens_predicted": 9}),
            ("no token count", {"stop_type": "eos"}),
            ("no reply at all", None),
            ("not a dict", "eos"),
            ("empty dict", {}),
            ("unknown stop_type", {"stop_type": "surprise", "tokens_predicted": 3}),
            ("word with no string", {"stop_type": "word", "tokens_predicted": 4}),
            ("token count is a bool", {"stop_type": "eos", "tokens_predicted": True}),
    ):
        line = relied.stopped_clock(resp)
        if not line or not line.startswith("STOPPED:"):
            fails.append("silent or malformed on: " + label)
        if len(line.strip()) < len("STOPPED: x"):
            fails.append("said nothing useful on: " + label)

    # an unrecognised value is reported AS GIVEN, never mapped onto a known one
    odd = relied.stopped_clock({"stop_type": "surprise", "tokens_predicted": 3})
    if "surprise" not in odd:
        fails.append("an unrecognised stop_type was not reported as given")
    for known in ("eos at", "cap reached"):
        if known in odd:
            fails.append("an unrecognised stop_type was mapped onto " + known)

    # ---- 3. NO BEHAVIOUR CHANGE. Nothing here ends a completion. -----------
    src = open(os.path.join(HERE, "relied.py"), encoding="utf-8").read()
    start = src.find("def stopped_clock(")
    fn = src[start:src.find("\ndef ", start + 1)]
    # The PAYLOAD keys, quoted. Bare "stop" would match stop_type in a function
    # whose entire job is reading stop_type -- a guard firing on the word it
    # exists to protect.
    for banned in ('logit_bias', 'ignore_eos', 'n_predict', '"stop"', "'stop'"):
        if banned in fn:
            fails.append("stopped_clock touches generation: " + banned)
    run_src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if "logit_bias" in run_src or "ignore_eos" in run_src:
        fails.append("run.py gained a way to lift EOS — that awaits his ruling")

    # ---- 4. the span that used to vanish is NAMED -------------------------
    resp = {"gt_relied": {"asked": 0.01, "file": 0.67}}
    unread = relied.unaccounted_spans(resp, ["asked", "file", "hold"])
    if unread != ["hold"]:
        fails.append("a placed span with no reading was not named: " + str(unread))
    line = relied.masses_clock([("asked", 0.01), ("file", 0.67)], unread)
    if "hold" not in line:
        fails.append("the clock dropped a span that came back unread")
    if "0.00" in line:
        fails.append("an unread span was shown as a zero — that is a reading it "
                     "never took")

    # all placed, all read: no noise added
    clean = relied.masses_clock([("asked", 0.01)], [])
    if relied.NO_READING_FOR in clean:
        fails.append("clean turn grew a spurious unread notice")

    # hook silent entirely: that is a DIFFERENT absence, already named
    if relied.unaccounted_spans({}, ["asked", "file"]) != []:
        fails.append("a silent hook must not report every span as unread — it "
                     "would bury the real cause under a list")

    # placed, none read at all
    only = relied.masses_clock([], ["asked"])
    if "asked" not in only or only == relied.NONE_PLACED:
        fails.append("spans placed but none read must not read as none placed")

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — stop disclosure: three endings told apart, nothing goes quiet, "
          "no behaviour change, unread spans named")
    return 0


if __name__ == "__main__":
    sys.exit(run())
