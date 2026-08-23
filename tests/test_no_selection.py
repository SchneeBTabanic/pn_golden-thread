#!/usr/bin/env python3
"""A number standing in for his meaning must not appear as an API."""
import ast
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN_FUNCS = {
    "search", "rank", "select", "relevance", "embed",
    "most_relevant_checks", "all_checks", "checks_for",
    "retrieve", "cosine",
}
FORBIDDEN_NAMES = {"_REGISTRY"}


def run():
    fails = []
    for dirpath, dirnames, files in os.walk(HERE):
        dirnames[:] = [d for d in dirnames
                       if d != "__pycache__"
                       and d != "site-packages"
                       and not d.startswith(".venv")]
        if "__pycache__" in dirpath or "site-packages" in dirpath:
            continue
        if "/.venv" in dirpath.replace("\\", "/"):
            continue
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            src = open(path, encoding="utf-8").read()
            try:
                tree = ast.parse(src)
            except SyntaxError as e:
                fails.append(f"{path}: {e}")
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name in FORBIDDEN_FUNCS:
                        fails.append(f"{path} defines {node.name}()")
                if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
                    fails.append(f"{path} names {node.id}")
                if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_NAMES:
                    fails.append(f"{path} names {node.attr}")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — no selector, ranker, embedder, or _REGISTRY in this tree")
    return 0


if __name__ == "__main__":
    sys.exit(run())
