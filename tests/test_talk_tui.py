#!/usr/bin/env python3
"""Headless Textual pilot: compose is not send; prompt advances; talk tab stays."""
import asyncio
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

WEB_SITE = (os.environ.get("GT_WEB_SITE") or "").strip()
if WEB_SITE and os.path.isdir(WEB_SITE) and WEB_SITE not in sys.path:
    sys.path.insert(0, WEB_SITE)


def run():
    try:
        import textual  # noqa: F401
    except ImportError:
        print("PASS — talk_tui textual pilot SKIPPED (textual not installed)")
        return 0
    return asyncio.run(_run())


async def _run():
    import talk_tui
    from textual.widgets import Label, TextArea, TabbedContent, TabPane

    fails = []
    app = talk_tui._textual_app(
        boot_note="window: 2 turn(s) after last /forget")
    async with app.run_test() as pilot:
        prompt = str(app.query_one("#prompt", Label).content)
        if prompt != "you @ turn 1 › ":
            fails.append("prompt start: " + repr(prompt))
        box = app.query_one("#entry", TextArea)
        if not getattr(box, "soft_wrap", True):
            fails.append("compose box is not soft-wrapped")
        log = app.query_one("#log")
        log_text = "\n".join(str(x) for x in getattr(log, "lines", []) or [])
        if "window: 2 turn(s)" not in log_text:
            fails.append("window clock did not reach the talk log")

        # Enter is a new line. It must not send. That is the defect this
        # shell exists to dissolve: a Return that locked the wording.
        box.text = "draft that is not ready"
        await pilot.press("enter")
        await pilot.pause()
        prompt = str(app.query_one("#prompt", Label).content)
        if prompt != "you @ turn 1 › ":
            fails.append("Enter sent the draft: " + repr(prompt))
        if "draft that is not ready" not in box.text:
            fails.append("Enter ate the draft: " + repr(box.text))

        # Send is a named action. The draft can hold more than one line.
        box.text = "one\nstill editing"
        await app.action_send()
        await pilot.pause()
        prompt = str(app.query_one("#prompt", Label).content)
        if prompt != "you @ turn 2 › ":
            fails.append("send did not advance: " + repr(prompt))
        you_lines = [t for (_, r, t) in app._transcript.lines if r == "YOU"]
        if you_lines[:1] != ["one\nstill editing"]:
            fails.append("multiline draft was flattened: " + repr(you_lines[:1]))
        if box.text.strip():
            fails.append("send left the draft: " + repr(box.text))

        for msg in ("two", "three"):
            box.text = msg
            await app.action_send()
            await pilot.pause()
        prompt = str(app.query_one("#prompt", Label).content)
        if prompt != "you @ turn 4 › ":
            fails.append("prompt after 3 sends: " + repr(prompt))
        roles = [r for (_, r, _) in app._transcript.lines]
        for need in ("YOU", "ANSWER", "CLERK"):
            if need not in roles:
                fails.append(need + " missing from transcript")
        for banned in ("PROXY", "EXECUTOR", "WHISTLEBLOWER"):
            if banned in roles:
                fails.append("persona leaked into transcript: " + banned)

        # talk tab remains; /view opens another tab (not a 45% takeover)
        box.text = "/view 1"
        await app.action_send()
        await pilot.pause()
        tabs = app.query_one("#tabs", TabbedContent)
        panes = sorted(p.id for p in tabs.query(TabPane))
        if "talk" not in panes:
            fails.append("talk tab vanished after /view: " + repr(panes))
        if "turn-1" not in panes:
            fails.append("/view 1 did not open a tab: " + repr(panes))
        log = app.query_one("#log")
        if hasattr(log, "display") and log.display is False:
            fails.append("talk log hidden = blocking")

        box.text = "/view 3"
        await app.action_send()
        await pilot.pause()
        panes = [p.id for p in tabs.query(TabPane)]
        if set(panes) != {"talk", "turn-1", "turn-3"}:
            fails.append("second view drifted: " + repr(panes))

        box.text = "/view 1"
        await app.action_send()
        await pilot.pause()
        panes = [p.id for p in tabs.query(TabPane)]
        if panes.count("turn-1") != 1:
            fails.append("/view 1 duplicated: " + repr(panes))
        if tabs.active != "turn-1":
            fails.append("/view 1 did not focus: " + repr(tabs.active))

        await pilot.press("escape")
        await pilot.pause()
        if tabs.active != "talk":
            fails.append("Esc did not return to talk: " + repr(tabs.active))
        panes = [p.id for p in tabs.query(TabPane)]
        if "turn-1" not in panes or "turn-3" not in panes:
            fails.append("Esc disposed tabs: " + repr(panes))

        box.text = "/close 1"
        await app.action_send()
        await pilot.pause()
        panes = [p.id for p in tabs.query(TabPane)]
        if "turn-1" in panes:
            fails.append("/close 1 left the pane: " + repr(panes))
        if "turn-3" not in panes:
            fails.append("/close 1 dropped the other tab: " + repr(panes))

        # Keys that must send: Ctrl+S, Ctrl+Enter, and Ctrl+J (the LF
        # many TTYs emit for Ctrl+Enter). Enter already proved it does not.
        before = len([t for (_, r, t) in app._transcript.lines if r == "YOU"])
        box.text = "from ctrl+s"
        await pilot.press("ctrl+s")
        await pilot.pause()
        box.text = "from ctrl+enter"
        await pilot.press("ctrl+enter")
        await pilot.pause()
        box.text = "from ctrl+j"
        await pilot.press("ctrl+j")
        await pilot.pause()
        you_lines = [t for (_, r, t) in app._transcript.lines if r == "YOU"]
        if "from ctrl+s" not in you_lines:
            fails.append("ctrl+s did not send: " + repr(you_lines))
        if "from ctrl+enter" not in you_lines:
            fails.append("ctrl+enter did not send: " + repr(you_lines))
        if "from ctrl+j" not in you_lines:
            fails.append("ctrl+j did not send: " + repr(you_lines))
        after = len(you_lines)
        if after != before + 3:
            fails.append("send keys count drifted: " + repr((before, after)))

        # Ctrl+C copies. It must not quit.
        app.action_copy()
        await pilot.pause()
        prompt = str(app.query_one("#prompt", Label).content)
        if "you @" not in prompt:
            fails.append("ctrl+c copy quit the shell")

    src = open(os.path.join(HERE, "talk_tui.py"), encoding="utf-8").read()
    if "on_input_submitted" in src:
        fails.append("Input-submit path is back — Enter would send again")
    if "from textual.widgets import Input" in src or "Input(" in src:
        fails.append("single-line Input is back")
    if "ctrl+enter,ctrl+s" not in src:
        fails.append("footer send keys drifted")
    if "ctrl+j" not in src:
        fails.append("ctrl+j LF fallback for Ctrl+Enter is missing")
    if "_compose_box_class" not in src:
        fails.append("ComposeBox is gone — TextArea can swallow send")
    if "action_copy_or_quit" in src:
        fails.append("ctrl+c still quits when copy finds nothing")
    if "def action_copy(" not in src:
        fails.append("ctrl+c copy action missing")
    if "RichLog" in src:
        fails.append("RichLog is back — drag-select cannot highlight")
    if "from textual.widgets import Log" not in src and "Log," not in src:
        fails.append("selectable Log widget missing")

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — talk_tui: Enter composes, send sends, no three personas")
    return 0


if __name__ == "__main__":
    sys.exit(run())
