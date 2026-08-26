"""
talk_tui.py — the compose-and-edit talk shell.

WHY THIS EXISTS. The old `input()` line sent on Return. A wrap, or a
Return meant as a new line, locked the wording: backspace could not walk
back through the draft. On a local model that takes a long time to reply,
that is a question you cannot unsay. This shell is a TextArea: Enter
starts a new line, arrows and backspace walk the whole draft, Ctrl+Enter
or Ctrl+S sends. You send when you mean it.

PROVENANCE. Layout ideas lifted from GTPS-Agent/viewer_textual.py, then
corrected by what Schnee already tested in pn_scribe-wb/viewer/scribe_viewer.py:
a permanent 45% side split "takes over a portion of the screen and makes
everything else smaller." A modal (one view at a time) was rejected. Several
views at once is the requirement. So the conversation is the FIRST TAB, full
width, and summons open beside it as more tabs. The compose box stays under
every tab.

WHAT IT IS NOT. Not GTPS-Agent. No EXECUTOR/WHISTLEBLOWER/PROXY panels.
The face is YOU + ANSWER. Python clocks are CLERK lines, quieter, the same
words run.py already prints on stderr. /shape is a summons tab, not a third
persona. /proxy is gone.

WHAT IT DOES NOT TOUCH. llama-hook, RELIED, HOLD_BANNER, the grammar pair,
dial/press math. The diary is still written by run.py's record path. Kill
this shell and only prettiness is lost.

  python3 run.py                 TTY: this shell, live
  python3 run.py --repl          the old one-line input()
  python3 talk_tui.py            stub (no model, no TTY needed for tests)
  python3 talk_tui.py --live     needs llama-server, same Talk.step as run.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from talk_core import Transcript, prompt_label, turn_boundary  # noqa: E402

# Textual lives in the venv named by GT_WEB_SITE.
WEB_SITE = (os.environ.get("GT_WEB_SITE") or "").strip()
if WEB_SITE and os.path.isdir(WEB_SITE) and WEB_SITE not in sys.path:
    sys.path.insert(0, WEB_SITE)

LOG_PANE = "talk"
TAB_LABEL_MAX = 16
SUMMONS = (
    "/views", "/history", "/walk", "/sheet", "/bind", "/keep", "/comment",
    "/shape", "/probe",
    "/held", "/open", "/fold", "/inquire", "/bearings", "/reset",
    "/sequel", "/raw", "/help", "/pile", "/law", "/declared",
    "/model",
)


def _stub_responder(text):
    """Headless default. Never a model. Returns (answer, clerk, tab_name, tab_body)."""
    low = (text or "").strip()
    if low.startswith("/view"):
        return "", "", "", ""
    if low == "/help":
        body = "talk tab is the conversation. summons open other tabs. /view N derives a turn."
        return "", "", "help", body
    if low in ("/exit", "/quit"):
        return "", "", "", ""
    return "echo:" + text, "FETCHED: none", "", ""


def make_live_responder():
    """Drive run.Talk so the TUI cannot grow a second turn()."""
    import run as runmod
    talk = runmod.Talk()
    rc = talk.boot()
    if rc:
        raise SystemExit("Talk.boot refused (no local model, or a pair is missing)")

    def responder(text):
        step = talk.step(text)
        tab_name = step.tab or ""
        tab_body = step.tab_body or ""
        return step.face, step.clerk, tab_name, tab_body

    return responder, runmod.window_status()


def _tab_label(name):
    s = str(name or "")
    if len(s) <= TAB_LABEL_MAX:
        return s
    return s[: TAB_LABEL_MAX - 1] + "…"


def _parse_view(cmd):
    parts = (cmd or "").split()
    if len(parts) != 2:
        return None
    try:
        n = int(parts[1])
    except ValueError:
        return None
    if n < 1:
        return None
    return n


def _compose_box_class():
    """TextArea that cannot swallow send. Enter stays a new line."""
    from textual.binding import Binding
    from textual.widgets import TextArea

    class ComposeBox(TextArea):
        BINDINGS = [
            Binding("ctrl+enter", "app.send", "send", priority=True, show=False),
            Binding("ctrl+s", "app.send", "send", priority=True, show=False),
            Binding("ctrl+j", "app.send", "send", priority=True, show=False),
        ]

        async def _on_key(self, event):
            if event.key in ("ctrl+enter", "ctrl+s", "ctrl+j"):
                event.stop()
                event.prevent_default()
                await self.app.run_action("send")
                return
            await super()._on_key(event)

    return ComposeBox


def _log_write(log, text):
    """Log.write_line per physical line. The log widget must support drag-select."""
    lines = str(text).splitlines()
    if not lines:
        log.write_line("")
        return
    for line in lines:
        log.write_line(line)


class TalkApp:
    """Bound later so tests can import this module when Textual is absent."""

    BINDINGS = [
        ("ctrl+c", "copy", "copy"),
        ("ctrl+q", "quit", "quit"),
        ("escape", "show_talk", "talk tab"),
        ("ctrl+enter", "send", "send"),
        ("ctrl+s", "send", "send"),
        ("ctrl+j", "send", "send"),
    ]
    ALLOW_SELECT = True
    CSS = """
    #tabs { height: 1fr; }
    #log { border: round $primary; height: 1fr; }
    #promptbar { height: 8; }
    #entry { height: 6; border: round $accent; }
    """

    def __init__(self, responder=None, boot_note=""):
        super().__init__()
        self._responder = responder or _stub_responder
        self._boot_note = boot_note or ""
        self._transcript = Transcript()
        self._next_turn = 1
        self._quit_requested = False
        self._busy = False

    def compose(self):
        from textual.app import ComposeResult
        from textual.containers import Vertical
        from textual.widgets import (
            Log, Label, Footer, TabbedContent, TabPane,
        )
        del ComposeResult
        with TabbedContent(id="tabs"):
            with TabPane("talk", id=LOG_PANE):
                yield Log(id="log", highlight=False)
        with Vertical(id="promptbar"):
            yield Label(prompt_label(self._next_turn), id="prompt")
            yield _compose_box_class()(
                id="entry",
                soft_wrap=True,
                compact=True,
                show_line_numbers=False,
                placeholder=(
                    "Enter = new line.  Ctrl+Enter or Ctrl+S = send.  "
                    "Backspace and arrows walk the whole draft."
                ),
            )
        yield Footer()

    def on_mount(self):
        from textual.widgets import TextArea, Log
        log = self.query_one("#log", Log)
        _log_write(log, "golden-thread talk shell. Compose, then send. The diary is the file.")
        _log_write(log, "Enter starts a new line. Ctrl+S sends. Ctrl+C copies (last answer if nothing is selected). Ctrl+Q quits.")
        _log_write(log, "YOU + ANSWER in this tab. Clocks are clerk lines, not a second face.")
        _log_write(log, "Summons (/walk /comment /shape /probe /views /history) open tabs. Esc returns here.")
        if self._boot_note:
            _log_write(log, self._boot_note)
        self.query_one("#entry", TextArea).focus()

    def _box(self):
        from textual.widgets import TextArea
        return self.query_one("#entry", TextArea)

    async def action_send(self):
        """Send the draft. Enter does not do this — Enter is a new line."""
        if self._busy:
            self.bell()
            return
        text = self._box().text.strip()
        if not text:
            return
        self._box().text = ""
        if text in ("/exit", "/quit"):
            self.exit()
            return
        if text.startswith("/view"):
            await self._open_view(text)
            return
        if text.startswith("/close"):
            await self._close(text)
            return
        if text in ("/hide", "/terminal"):
            self.action_show_talk()
            return
        self._busy = True
        try:
            await self._exchange(text)
        finally:
            self._busy = False
            self._box().focus()

    async def _open_view(self, cmd):
        from textual.widgets import TabbedContent, TabPane, Static
        from textual.containers import VerticalScroll
        from rich.text import Text
        n = _parse_view(cmd)
        if n is None:
            self.bell()
            return
        tabs = self.query_one("#tabs", TabbedContent)
        pane_id = "turn-" + str(n)
        have = {p.id for p in tabs.query(TabPane)}
        if pane_id not in have:
            lines = self._transcript.view_of(n)
            body = VerticalScroll(Static(Text("\n".join(lines))))
            await tabs.add_pane(TabPane(_tab_label("turn " + str(n)), body, id=pane_id))
        tabs.active = pane_id
        self._box().focus()

    async def _close(self, cmd):
        from textual.widgets import TabbedContent, TabPane
        parts = cmd.split()
        tabs = self.query_one("#tabs", TabbedContent)
        if len(parts) < 2:
            self.action_show_talk()
            return
        token = parts[1]
        pane_id = "turn-" + token if token.isdigit() else token
        have = {p.id for p in tabs.query(TabPane)}
        if pane_id in have and pane_id != LOG_PANE:
            await tabs.remove_pane(pane_id)
        tabs.active = LOG_PANE
        self._box().focus()

    def action_show_talk(self):
        from textual.widgets import TabbedContent
        self.query_one("#tabs", TabbedContent).active = LOG_PANE
        self._box().focus()

    def action_copy(self):
        """Copy. Never quit. Ctrl+Q is quit.

        Drag-select on the log if the widget can highlight. If the mouse
        highlights nothing, copy the last ANSWER, then the whole transcript.
        """
        sel = None
        try:
            sel = self.screen.get_selected_text()
        except Exception:
            sel = None
        if sel:
            self.copy_to_clipboard(sel)
            return
        try:
            from textual.widgets import TextArea
            box = self.query_one("#entry", TextArea)
            selected = getattr(box, "selected_text", "") or ""
        except Exception:
            selected = ""
        if selected:
            self.copy_to_clipboard(selected)
            return
        answers = [t for (_, r, t) in self._transcript.lines if r == "ANSWER"]
        if answers:
            self.copy_to_clipboard(answers[-1])
            return
        blob = "\n".join(self._transcript.render())
        if blob.strip():
            self.copy_to_clipboard(blob)
            return
        try:
            from textual.widgets import Log
            text = "\n".join(self.query_one("#log", Log).lines)
        except Exception:
            text = ""
        if text.strip():
            self.copy_to_clipboard(text)
            return
        self.bell()

    async def _exchange(self, text):
        from textual.widgets import Label, Log, TabbedContent, TabPane, Static
        from textual.containers import VerticalScroll
        from rich.text import Text
        turn = self._next_turn
        log = self.query_one("#log", Log)
        _log_write(log, turn_boundary(turn, width=(self.size.width or 60)))
        self._transcript.add(turn, "YOU", text)
        _log_write(log, "YOU: " + text)
        answer, clerk, tab_name, tab_body = self._responder(text)
        if answer:
            self._transcript.add(turn, "ANSWER", answer)
            _log_write(log, answer)
        if clerk:
            self._transcript.add(turn, "CLERK", clerk)
            _log_write(log, clerk)
        self._next_turn = turn + 1
        self.query_one("#prompt", Label).update(prompt_label(self._next_turn))
        if tab_name and tab_body:
            tabs = self.query_one("#tabs", TabbedContent)
            pane_id = "v-" + tab_name.replace(":", "-").replace(" ", "-")
            have = {p.id for p in tabs.query(TabPane)}
            if pane_id not in have:
                body = VerticalScroll(Static(Text(tab_body)))
                await tabs.add_pane(
                    TabPane(_tab_label(tab_name), body, id=pane_id))
            tabs.active = pane_id
        self._box().focus()


def _textual_app(responder=None, boot_note=""):
    from textual.app import App
    from textual.binding import Binding

    class BoundTalkApp(TalkApp, App):
        # BINDINGS must sit on the App subclass so Textual's metaclass
        # collects them. TalkApp is a mixin and is not itself an App.
        # ctrl+enter is priority so the TextArea cannot swallow send.
        # ctrl+j is the LF many TTYs send for Ctrl+Enter; not advertised.
        BINDINGS = [
            Binding("ctrl+c", "copy", "copy", priority=True),
            Binding("ctrl+q", "quit", "quit"),
            Binding("escape", "show_talk", "talk tab"),
            Binding(
                "ctrl+enter,ctrl+s",
                "send",
                "send",
                priority=True,
                key_display="ctrl+enter, ctrl+s",
            ),
            Binding("ctrl+j", "send", "send", priority=True, show=False),
        ]
        CSS = TalkApp.CSS
        ALLOW_SELECT = True

    return BoundTalkApp(responder=responder, boot_note=boot_note)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    live = "--live" in argv
    try:
        import textual  # noqa: F401
    except ImportError:
        raise SystemExit(
            "textual not installed — set GT_WEB_SITE to the venv "
            "site-packages (see env.example.sh)")
    responder, boot_note = (make_live_responder() if live else (None, ""))
    app = _textual_app(responder=responder, boot_note=boot_note)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
