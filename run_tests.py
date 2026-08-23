#!/usr/bin/env python3
"""Every test. No model. No server. No pytest.

    python3 run_tests.py
"""
import os
import pathlib
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

SUITES = [
    "tests/test_arithmetic.py",
    "tests/test_echo.py",
    "tests/test_quantities.py",
    "tests/test_file_read.py",
    "tests/test_law.py",
    "tests/test_no_selection.py",
    "tests/test_examine.py",
    "tests/test_tape.py",
    "tests/test_walk.py",
    "tests/test_path_stack.py",
    "tests/test_turn_record.py",
    "tests/test_backend.py",
    "tests/test_skin.py",
    "tests/test_held_skin.py",
    "tests/test_export.py",
    "tests/test_gf_backend.py",
    "tests/test_hold.py",
    "tests/test_probe.py",
    "tests/test_relied.py",
    "tests/test_dial_press.py",
    "tests/test_prior_record.py",
    "tests/test_web.py",
    "tests/test_strip.py",
    "tests/test_talk_core.py",
    "tests/test_talk_tui.py",
]


def _guard_no_regex():
    mod = "re"
    calls = ("compile", "search", "match", "sub", "split", "finditer",
             "fullmatch", "escape")
    needles = [mod + "." + c + "(" for c in calls]
    import_forms = ("import " + mod, "from " + mod + " ")
    bad = []
    pyfiles = []
    for f in sorted(pathlib.Path(HERE).rglob("*.py")):
        skip = False
        for part in f.parts:
            if part.startswith(".venv") or part == "site-packages":
                skip = True
                break
        if skip:
            continue
        pyfiles.append(f)
        text = f.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if (stripped == import_forms[0]
                    or stripped.startswith(import_forms[0] + " ")
                    or stripped.startswith(import_forms[1])):
                bad.append((f, i, stripped))
                continue
            for needle in needles:
                if needle in line:
                    bad.append((f, i, stripped))
                    break
    if bad:
        for f, i, line in bad:
            print(f"FAIL — regex at {f}:{i}: {line}")
        return 1
    n = len(pyfiles)
    print(f"PASS — no regular expressions in any of {n} python files")
    return 0


def _guard_grammar():
    import run as runmod
    rc = 0
    for name in ("grammar.gbnf", "grammar_held.gbnf"):
        grammar = open(os.path.join(HERE, name), encoding="utf-8").read()
        try:
            runmod._check_grammar_one_line_per_rule(grammar, name)
        except SystemExit as e:
            print(f"FAIL — grammar guard: {e}")
            rc = 1
            continue
        rules = [l for l in grammar.splitlines()
                 if l.strip() and not l.strip().startswith("#")]
        print(f"PASS — {name}: {len(rules)} rules, each on one line")
    return rc


def _guard_no_proxy():
    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    fails = []
    if '"/proxy"' in src or "'/proxy'" in src:
        fails.append("run.py still offers /proxy")
    if "def proxy(" in open(os.path.join(HERE, "model.py"), encoding="utf-8").read():
        fails.append("model.py still defines proxy()")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — /proxy is gone; /shape is the summons")
    return 0


def _guard_walk_is_summoned():
    """Talk must not wait for Dango or file a generated @act/@path."""
    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    fails = []
    if "PATH: Dango Japanese" in src:
        fails.append("run.py still runs the path stack on every answer")
    if "extra_tags=None" not in src:
        fails.append("run.py must record turns with extra_tags=None")
    if 'low == "/walk"' not in src:
        fails.append("/walk summons is missing")
    if 'low == "/comment"' not in src:
        fails.append("/comment summons is missing")
    if 'low == "/probe"' not in src and 'low.startswith("/probe")' not in src:
        fails.append("/probe summons is missing")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — talk does not tag; /walk /comment /probe are summons")
    return 0


def _guard_path_is_not_substring():
    """Python must not decide leftover speech by word overlap."""
    fails = []
    run_src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    tape_src = open(os.path.join(HERE, "tape.py"), encoding="utf-8").read()
    model_src = open(os.path.join(HERE, "model.py"), encoding="utf-8").read()
    if "sequel_on_path" in run_src or "sequel_on_path" in tape_src:
        fails.append("sequel_on_path is still in the runtime")
    if "stay on this path" in run_src:
        fails.append("run.py still stuffs !path into the Executor prompt")
    if "def look(" not in model_src:
        fails.append("model.look is missing")
    if "def _as_chat(" not in model_src:
        fails.append("comment/shape/look need granite chat wrap")
    if "summon_look" not in run_src:
        fails.append("run.py must summon a look on declared leftover speech")
    stack_src = open(os.path.join(HERE, "path_stack.py"), encoding="utf-8").read()
    if "tag_sheet_live_core" not in run_src:
        fails.append("Granite look must be handed the live-core tag sheet")
    if "granite_l2_tags" not in stack_src:
        fails.append("path_stack must have granite_l2_tags")
    run_chunk = stack_src.split("def run_stack(", 1)[1].split(
        "def stack_as_walk_text(", 1)[0]
    if "dango_l2_tags(" in run_chunk:
        fails.append("run_stack still asks Dango for English L2")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — !path does not score by substring; a second span looks")
    return 0


def _guard_no_python_scribe_runtime():
    """Phase 1 clean swap: the talk runtime does not call scribe.py."""
    fails = []
    for name in ("pile_io.py", "run.py", "turn_record.py"):
        src = open(os.path.join(HERE, name), encoding="utf-8").read()
        if "scribe.py" in src or "GT_SCRIBE" in src:
            fails.append(f"{name} still names scribe.py / GT_SCRIBE")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — talk runtime is gForth keep, not python scribe")
    return 0


def main():
    rc = 0
    for rel in SUITES:
        print()
        print("=" * 70)
        print(rel)
        print("=" * 70)
        p = subprocess.run([sys.executable, os.path.join(HERE, rel)])
        if p.returncode != 0:
            rc = 1
    print()
    print("=" * 70)
    print("guards")
    print("=" * 70)
    rc |= _guard_no_regex()
    rc |= _guard_grammar()
    rc |= _guard_no_proxy()
    rc |= _guard_walk_is_summoned()
    rc |= _guard_path_is_not_substring()
    rc |= _guard_no_python_scribe_runtime()
    print()
    print("ALL PASSED" if rc == 0 else "FAILED")
    return rc


if __name__ == "__main__":
    sys.exit(main())
