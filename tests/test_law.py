#!/usr/bin/env python3
"""law.py exposes no selector. The JSON is the inoculated text of record."""
import ast
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import law as law_module  # noqa: E402

FORBIDDEN = {
    "search", "rank", "select", "relevance", "embed",
    "most_relevant_checks", "all_checks", "checks_for",
}


def run():
    fails = []
    tree = ast.parse(open(os.path.join(HERE, "law.py"), encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in FORBIDDEN:
                fails.append(f"law.py defines {node.name}()")
    law = law_module.load()
    if len(law) < 40:
        fails.append(f"expected the 48-clause file, got {len(law)}")
    try:
        law.get("99999")
        fails.append("get() did not refuse an unknown id")
    except KeyError:
        pass
    import json
    data = json.load(open(law.source_path, encoding="utf-8"))
    for c in data.get("clauses", []):
        if "applies_when" in c:
            fails.append(f"clause {c.get('id')} has applies_when")
    slab = law_module.law_text(law)
    if len(slab) < 10000:
        fails.append(f"law_text too short to be the 48: {len(slab)} chars")
    first_id = law.clauses[0].id
    last_id = law.clauses[-1].id
    if not slab.startswith(first_id + ".") or last_id + "." not in slab:
        fails.append("law_text is not file order of the loaded clauses")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print(f"PASS — law.py has no selector; {len(law)} clauses from")
    print(f"       {law.source_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
