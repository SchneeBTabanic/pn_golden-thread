#!/usr/bin/env python3
"""auto prefers llama-server. Ollama is a client."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import model  # noqa: E402


def run():
    fails = []
    old_up_l, old_up_o = model._llama_up, model._ollama_up
    old_b = os.environ.get("GT_BACKEND")
    os.environ["GT_BACKEND"] = "auto"
    try:
        model._llama_up = lambda: True
        model._ollama_up = lambda: True
        if model.backend() != "llama":
            fails.append(f"auto with both up -> {model.backend()!r}, want llama")
        model._llama_up = lambda: False
        model._ollama_up = lambda: True
        if model.backend() != "ollama":
            fails.append(f"auto with only ollama -> {model.backend()!r}")
        model._llama_up = lambda: False
        model._ollama_up = lambda: False
        if model.backend() is not None:
            fails.append("auto with neither up should be None")
        src = open(os.path.join(HERE, "model.py"), encoding="utf-8").read()
        # The default path must try llama first. A comment is not enough:
        # the first _*_up() call in backend() under auto must be llama.
        fn = src.split("def backend():", 1)[1].split("def health():", 1)[0]
        if "# auto:" not in fn:
            fails.append("auto path is not marked")
        else:
            auto = fn.split("# auto:", 1)[1]
            if auto.find("_llama_up") > auto.find("_ollama_up"):
                fails.append("auto path calls _ollama_up before _llama_up")
    finally:
        model._llama_up, model._ollama_up = old_up_l, old_up_o
        if old_b is None:
            os.environ.pop("GT_BACKEND", None)
        else:
            os.environ["GT_BACKEND"] = old_b
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — auto prefers llama-server")
    return 0


if __name__ == "__main__":
    sys.exit(run())
