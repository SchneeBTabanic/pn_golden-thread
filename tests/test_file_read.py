#!/usr/bin/env python3
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import file_read  # noqa: E402


def run():
    fails = []
    r = file_read.read_placed("")
    if r.ok:
        fails.append("empty path was accepted")
    r = file_read.read_placed("/no/such/file/gt-test-missing-xyz")
    if r.ok or "does not exist" not in r.refused:
        fails.append(f"missing file: {r}")
    r = file_read.read_placed("~Desktop/x.html")
    if r.ok or "~/" not in r.refused:
        fails.append("tilde without slash must be named, not expanduser: "
                     + repr(r.refused))
    with tempfile.TemporaryDirectory() as d:
        r = file_read.read_placed(d)
        if r.ok or "directory" not in r.refused:
            fails.append(f"directory not refused: {r}")
        path = os.path.join(d, "note.txt")
        body = "hello from a placed file\nsecond line\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        r = file_read.read_placed(path)
        if not r.ok or r.content != body:
            fails.append(f"plain file not read whole: {r}")
        binpath = os.path.join(d, "x.bin")
        with open(binpath, "wb") as f:
            f.write(b"ok\x00no")
        r = file_read.read_placed(binpath)
        if r.ok or "NUL" not in r.refused:
            fails.append(f"binary not refused: {r}")
        big = os.path.join(d, "big.txt")
        old = file_read.MAX_BYTES
        file_read.MAX_BYTES = 8
        try:
            with open(big, "w", encoding="utf-8") as f:
                f.write("0123456789")
            r = file_read.read_placed(big)
            if r.ok or "exceeds cap" not in r.refused:
                fails.append(f"oversize not refused: {r}")
        finally:
            file_read.MAX_BYTES = old
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — file: reads whole or refuses; no partial, no selector")
    return 0


if __name__ == "__main__":
    sys.exit(run())
