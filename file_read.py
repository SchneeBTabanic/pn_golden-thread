"""
file_read.py — the human places a file. This program places inert text, or refuses.

No glob. No path inferred from prose. No paragraph selector.
A missing file, an unreadable file, a directory, an unknown binary, or a
file over the size cap is a named refusal — never a silent partial read.

HTML / PDF / docx / odt / epub are reduced at this boundary (strip.py).
Plain UTF-8 is placed as itself. file: is content, not an obligation.
"""
import os
from dataclasses import dataclass

import strip

# Placed TEXT cap you can count. Source binaries may be larger.
MAX_BYTES = int(os.environ.get("GT_FILE_MAX_BYTES", "200000"))
SOURCE_MAX = int(os.environ.get("GT_SOURCE_MAX_BYTES", "8000000"))


@dataclass
class FileRead:
    ok: bool
    path: str
    content: str = ""
    refused: str = ""
    bytes_read: int = 0
    reduction: str = ""


def _oversize(n, cap, what):
    return (
        str(n) + " bytes exceeds cap " + str(cap) + ". "
        + "Set " + what + " or place a smaller file. Nothing was read.")


def read_placed(path: str) -> FileRead:
    """Read the file at `path` as inert text, or refuse with a reason."""
    raw = (path or "").strip()
    if not raw:
        return FileRead(ok=False, path="", refused="no path given")
    target = os.path.abspath(os.path.expanduser(raw))
    if not os.path.exists(target):
        return FileRead(ok=False, path=target, refused="does not exist")
    if os.path.isdir(target):
        return FileRead(ok=False, path=target,
                        refused="is a directory — name a file")
    if not os.path.isfile(target):
        return FileRead(ok=False, path=target, refused="not a regular file")
    try:
        size = os.path.getsize(target)
    except OSError as e:
        return FileRead(ok=False, path=target, refused=f"cannot stat ({e})")
    cap_src = max(SOURCE_MAX, MAX_BYTES)
    if size > cap_src:
        return FileRead(
            ok=False, path=target,
            refused=_oversize(size, cap_src, "GT_SOURCE_MAX_BYTES"))
    try:
        with open(target, "rb") as f:
            blob = f.read()
    except OSError as e:
        return FileRead(ok=False, path=target, refused=f"cannot read ({e})")

    text, note = strip.reduce_blob(blob, name=target, prefer="faithful")
    if note is not None and text is None:
        return FileRead(ok=False, path=target, refused=note, bytes_read=len(blob))
    if text is not None:
        placed = text.encode("utf-8")
        if len(placed) > MAX_BYTES:
            return FileRead(
                ok=False, path=target,
                refused=_oversize(len(placed), MAX_BYTES, "GT_FILE_MAX_BYTES"),
                bytes_read=len(blob))
        return FileRead(
            ok=True, path=target, content=text, bytes_read=len(blob),
            reduction=note or "")

    if b"\x00" in blob:
        return FileRead(ok=False, path=target,
                        refused="contains NUL bytes — treating as binary, "
                                "not placing in a prompt")
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        text = blob.decode("utf-8", errors="replace")
        if len(text.encode("utf-8")) > MAX_BYTES:
            return FileRead(
                ok=False, path=target,
                refused=_oversize(len(blob), MAX_BYTES, "GT_FILE_MAX_BYTES"))
        return FileRead(
            ok=True, path=target, content=text, bytes_read=len(blob),
            refused="decoded with replacement characters — not clean UTF-8. "
                    "The model will see U+FFFD where bytes were illegal.")
    if len(blob) > MAX_BYTES:
        return FileRead(
            ok=False, path=target,
            refused=_oversize(len(blob), MAX_BYTES, "GT_FILE_MAX_BYTES"))
    return FileRead(ok=True, path=target, content=text, bytes_read=len(blob))
