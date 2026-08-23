#!/usr/bin/env python3
"""Talk shell core: prompt stamp, named absence, no three-persona roles."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import talk_core  # noqa: E402
import talk_tui  # noqa: E402


def run():
    fails = []
    if talk_core.prompt_label(1) != "you @ turn 1 › ":
        fails.append("prompt drifted: " + repr(talk_core.prompt_label(1)))
    try:
        talk_core.prompt_label(0)
        fails.append("nonpositive prompt was accepted")
    except ValueError:
        pass
    rule = talk_core.turn_boundary(3, width=40)
    if "@@ turn 3" not in rule:
        fails.append("boundary lost the turn: " + repr(rule))

    t = talk_core.Transcript()
    t.add(1, "YOU", "hello")
    t.add(1, "ANSWER", "echo:hello")
    t.add(1, "CLERK", "FETCHED: none")
    t.add(2, "YOU", "two")
    t.add(2, "ANSWER", "echo:two")
    if t.turns() != [1, 2]:
        fails.append("turns drifted: " + repr(t.turns()))
    slice1 = t.view_of(1)
    if not any("hello" in ln for ln in slice1):
        fails.append("view_of lost turn 1")
    if any("echo:two" in ln for ln in slice1):
        fails.append("view_of leaked turn 2")
    missing = "\n".join(t.view_of(9))
    if "not in this session" not in missing:
        fails.append("missing turn was faked empty")

    # DNA: the stub never invents PROXY / three persona panels
    ans, clerk, tab, body = talk_tui._stub_responder("hi")
    if ans != "echo:hi":
        fails.append("stub answer drifted: " + repr(ans))
    if clerk != "FETCHED: none":
        fails.append("stub clerk drifted: " + repr(clerk))
    joined = ans + clerk + tab + body
    for banned in ("PROXY", "EXECUTOR", "WHISTLEBLOWER"):
        if banned in joined:
            fails.append("stub grew a persona: " + banned)
        if banned in open(os.path.join(HERE, "talk_tui.py"),
                          encoding="utf-8").read().split("WHAT IT IS NOT", 1)[1]:
            # the refusal paragraph names them; that is allowed
            pass
    src = open(os.path.join(HERE, "talk_tui.py"), encoding="utf-8").read()
    if "persona_panel" in src:
        fails.append("talk_tui copied persona_panel")
    if "PERSONA_STYLE" in src:
        fails.append("talk_tui copied PERSONA_STYLE")
    if "width: 45%" in src:
        fails.append("talk_tui shipped the rejected 45% split")
    if "TextArea" not in src:
        fails.append("talk_tui lost the compose TextArea")
    if "on_input_submitted" in src:
        fails.append("Enter-to-send path is back")

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — talk core is YOU/ANSWER/CLERK; absence named")
    return 0


if __name__ == "__main__":
    sys.exit(run())
