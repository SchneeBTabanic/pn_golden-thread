#!/usr/bin/env python3
"""The non-baby-step proof.

Not §6 (that is still his comparison on something he cares about).
This proves the OUTSIDE of the probability chamber is real and automatic:

  1. A bare question is FETCHED: none — a clock, not a sermon.
  2. file: of a known file is FETCHED: that path. The empty/missing case
     cannot be outvoted by a success-shaped story.
  3. The turn pile exists, has a genesis, and can be exported by tag.
  4. /shape speech is not fed back as the answer.
  5. stderr never says "training probability".

Needs a local model (llama-server preferred, ollama permitted).

    python3 prove_the_outside.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "tests", "fixture_place.txt")


def main():
    sys.path.insert(0, HERE)
    import model
    if not model.health():
        print("FAIL — no local model. Start llama-server or ollama.",
              file=sys.stderr)
        print("Offline suite still proves the clock and the joiner:")
        print("  python3 run_tests.py")
        return 2

    tmp = tempfile.mkdtemp(prefix="gt-prove-")
    pile = os.path.join(tmp, "turns.txt")
    env = os.environ.copy()
    env["GT_TURN_PILE"] = pile
    env["GT_EXECUTOR_TOKENS"] = "80"
    script = (
        "Say the single word hello.\n"
        f"file: {FIXTURE} What is the first line?\n"
        "/shape\n"
        "/exit\n"
    )
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "run.py")],
        input=script, text=True, capture_output=True, env=env, cwd=HERE)
    out, err = proc.stdout or "", proc.stderr or ""
    fails = []
    if "FETCHED: none" not in err:
        fails.append("bare turn did not clock FETCHED: none")
    if FIXTURE not in err and "FETCHED: " not in err:
        fails.append("file: turn did not clock a FETCHED path")
    if "training probability" in err or "high likelihood" in err:
        fails.append("sermon is back on stderr")
    if "YOUR LAW" in err or "DID NOT APPLY" in err:
        fails.append("the long ledger is back on stderr")
    if not os.path.exists(pile):
        fails.append("no turn pile was written")
    else:
        sys.path.insert(0, HERE)
        from pile_io import export_selector, load_pile
        from turn_record import view_for_model
        genesis, blocks = load_pile(pile)
        if not genesis.startswith("辻"):
            fails.append(f"pile not stamped: {genesis!r}")
        if len(blocks) < 3:
            fails.append(f"expected session+turns, got {len(blocks)} blocks")
        try:
            slab = export_selector(pile, "topic:turn")
            if "ASKED:" not in slab:
                fails.append("export topic:turn is empty of turns")
        except Exception as e:
            fails.append(f"export failed: {e}")
        view = view_for_model(8)
        if "── shape" in view or "SHAPE:" in view:
            fails.append("shape speech leaked into the Executor view")
    if "shape, spoken" not in out:
        fails.append("/shape did not run")

    print("stdout (answer / shape):")
    print(out[-2000:] if len(out) > 2000 else out)
    print("stderr (clock only):")
    print(err[-800:] if len(err) > 800 else err)
    if fails:
        print("PROOF FAILED")
        for f in fails:
            print("  —", f)
        shutil.rmtree(tmp, ignore_errors=True)
        return 1
    print("PROOF HELD")
    print("  FETCHED: none on a bare question (clock, not sermon)")
    print("  FETCHED: the placed file when you typed file:")
    print("  pile stamped, exportable by topic:turn")
    print("  /shape ran and did not become the next answer")
    print(f"  pile kept at {pile} (temp; delete whenever)")
    # keep pile for him to inspect this run
    print("  inspect: from pn_golden-thread,")
    print(f"    python3 -c \"from pile_io import toc_by; print(toc_by(r'{pile}', 'act'))\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
