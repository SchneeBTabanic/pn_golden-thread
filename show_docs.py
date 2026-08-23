#!/usr/bin/env python3
"""Doorway to the user docs. The pile is the truth. These are views.

    python3 show_docs.py           list the parts
    python3 show_docs.py start     which program to run
    python3 show_docs.py talk      how a turn works
    python3 show_docs.py doorway   how to read the docs
    python3 show_docs.py toc       scribe toc --by part
    python3 show_docs.py export    write derived .md views (disposable)
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "piles", "docs.txt")
SCRIBE = os.path.normpath(os.path.join(HERE, "..", "pn_scribe-wb", "scribe.py"))

PARTS = {
    "doorway": "part:doorway",
    "start": "part:how-to-start",
    "talk": "part:how-to-talk",
}

DERIVED = {
    "start": os.path.join(HERE, "GUIDE_derived_how-to-start.md"),
    "talk": os.path.join(HERE, "GUIDE_derived_how-to-talk.md"),
}


def _scribe(args):
    return subprocess.run(
        [sys.executable, SCRIBE] + args,
        text=True, capture_output=True)


def main():
    if not os.path.isfile(DOCS):
        print("docs pile missing:", DOCS, file=sys.stderr)
        return 1
    if len(sys.argv) < 2:
        print("User docs live in piles/docs.txt (scribe pile). Views:")
        print("  python3 show_docs.py start    — which file to run")
        print("  python3 show_docs.py talk     — how you engage")
        print("  python3 show_docs.py doorway  — how to read this pile")
        print("  python3 show_docs.py toc")
        print("  python3 show_docs.py export   — write disposable .md copies")
        return 0
    cmd = sys.argv[1].strip().lower()
    if cmd == "toc":
        p = _scribe(["toc", DOCS, "--by", "part"])
        print(p.stdout or p.stderr)
        return p.returncode
    if cmd == "export":
        rc = 0
        for name, sel in (("start", PARTS["start"]), ("talk", PARTS["talk"])):
            p = _scribe(["export", sel, DOCS, "--bare", "--joiner", "\n\n"])
            if p.returncode != 0 or not (p.stdout or "").strip():
                print("export failed:", name, p.stderr, file=sys.stderr)
                rc = 1
                continue
            header = (
                "# DERIVED VIEW — disposable. The pile is the truth.\n"
                f"# piles/docs.txt  {sel}\n"
                "# Regenerate: python3 show_docs.py export\n"
                "# Edit the pile (scribe), not this file.\n\n"
            )
            with open(DERIVED[name], "w", encoding="utf-8") as f:
                f.write(header + p.stdout)
            print("wrote", DERIVED[name])
        return rc
    if cmd in PARTS:
        p = _scribe(["export", PARTS[cmd], DOCS, "--bare", "--joiner", "\n\n"])
        if p.returncode != 0:
            print(p.stderr or "export failed", file=sys.stderr)
            return p.returncode
        print((p.stdout or "").rstrip())
        return 0
    print("unknown:", cmd, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
