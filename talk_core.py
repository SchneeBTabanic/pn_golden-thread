"""
talk_core.py — framework-free heart of the optional talk shell.

Descendant of GTPS-Agent/viewer_core.py (turn stamp, in-memory transcript,
derive-a-slice). Divergence is intended: that viewer modelled three persona
panels. This one models YOU + ANSWER + quieter CLERK. Shape is a summons,
not a third face. PROXY is not here.

No TTY, no Textual, no model, no disk. The diary remains the truth. Kill
the shell and only prettiness is lost.
"""

PROMPT_GLYPH = "›"


def prompt_label(next_turn):
    """The input prompt, stamped with the turn the typed line will become.
    Matches run.py: 'you @ turn N › ' (spaces around @ and turn)."""
    n = int(next_turn)
    if n < 1:
        raise ValueError("turn must be >= 1, got " + str(next_turn))
    return "you @ turn " + str(n) + " " + PROMPT_GLYPH + " "


def turn_boundary(turn, width=60):
    """A visible rule for the human's navigation. Not fed to the model."""
    n = int(turn)
    if n < 1:
        raise ValueError("turn must be >= 1, got " + str(turn))
    label = " @@ turn " + str(n) + " "
    if width <= len(label):
        return label.strip()
    pad = width - len(label)
    left = pad // 2
    return ("─" * left) + label + ("─" * (pad - left))


class Transcript:
    """In-memory scrollback: (turn, role, text). Disposable. Never a file.
    Roles we use: YOU, ANSWER, CLERK. Never EXECUTOR/WHISTLEBLOWER/PROXY."""

    def __init__(self):
        self._lines = []

    def add(self, turn, role, text):
        n = int(turn)
        if n < 1:
            raise ValueError("turn must be >= 1, got " + str(turn))
        self._lines.append((n, str(role), str(text)))

    @property
    def lines(self):
        return list(self._lines)

    def turns(self):
        seen = []
        for t, _, _ in self._lines:
            if t not in seen:
                seen.append(t)
        return seen

    def render(self, width=60):
        out, last = [], None
        for turn, role, text in self._lines:
            if turn != last:
                out.append(turn_boundary(turn, width))
                last = turn
            if role:
                out.append(role + ": " + text)
            else:
                out.append(text)
        return out

    def view_of(self, *turns):
        """Derive a disposable slice. A missing turn is named, never faked."""
        wanted = [int(t) for t in turns]
        for t in wanted:
            if t < 1:
                raise ValueError("turn must be >= 1, got " + str(t))
        present = set(self.turns())
        out, last = [], None
        for t in wanted:
            if t not in present:
                out.append(turn_boundary(t))
                out.append("(turn " + str(t) + ": not in this session)")
                last = t
                continue
            for turn, role, text in self._lines:
                if turn != t:
                    continue
                if turn != last:
                    out.append(turn_boundary(turn))
                    last = turn
                if role == "CLERK":
                    out.append(text)
                elif role:
                    out.append(role + ": " + text)
                else:
                    out.append(text)
        return out
