#!/usr/bin/env python3
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import walk  # noqa: E402


def run():
    fails = []
    reg = walk.load_register()
    if "touched" not in reg or "aspect" not in reg:
        fails.append("register missing seats")
    acc, ref, emp = walk.parse_walk(
        "@touched:proxy\n"
        "@aspect:prospective\n"
        "@act:put-a-question\n"
        "@because:not-a-reason\n"
        "@mystery:nope\n"
        "@awaits:the first citation\n"
        "EMPTY path\n"
        "@name:steiners-turn\n",
        reg,
    )
    keys = [k for k, _ in acc]
    if "touched" not in keys or "name" not in keys:
        fails.append(f"lost good tags: {acc}")
    if ("touched", "proxy") not in acc:
        fails.append("persona seat @touched:proxy not accepted")
    if any(k == "act" for k, _ in acc):
        fails.append("mouth-owned act was accepted")
    if not any("space" in r for r in ref):
        fails.append(f"space in awaits not refused: {ref}")
    if not any("unknown" in r for r in ref):
        fails.append(f"unknown key not refused: {ref}")
    if not any("closed-class" in r for r in ref):
        fails.append(f"bad grouping value not refused: {ref}")
    if "path" not in emp:
        fails.append(f"EMPTY path not recorded: {emp}")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — clerk accepts a walk of the register; invents nothing")
    return 0


if __name__ == "__main__":
    sys.exit(run())
