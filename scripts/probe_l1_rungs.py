#!/usr/bin/env python3
"""DIAG-L1 probes D1–D3. One Dango load. Does not change the walk."""
import sys
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import path_stack  # noqa: E402

# Builder-written translation of the clean 2+2 turn (four short sentences).
# ASKED: What is 2+2?
# ANSWERED: 2+2 is a mathematical operation that results in 4. However,
# based on your personal observation, you have counted 2. In standard
# mathematical terms, 2+2 equals 4.
JA_ASKED = "二たす二は何ですか。"
JA_ANSWERED = (
    "二たす二は四になる計算です。"
    "しかしあなたが目の前のものを数えたところ、二つでした。"
    "普通の数え方では二たす二は四です。"
)

INSTR = "会話の動きを短い日本語の一文で書く。英語は書かない。"

# Form-only exemplar: unrelated sewing, not copyable onto 2+2.
FORM_EX = (
    "人: 靴の底が剥がれた\n"
    "答え: 糸で縫い直した\n"
    "動き: 剥がれた底を縫い直す\n"
)

D3_STEM = (
    "朝、井戸端で水を汲んだ。桶は重く、肩に食い込んだ。"
    "帰り道、猫が石段で日向ぼっこをしていた。"
)


def looks(s):
    return path_stack.looks_japanese(s)


def main():
    print("loading Dango…", file=sys.stderr)
    if not path_stack._load_dango():
        print("REFUSED — " + path_stack._dango["error"], file=sys.stderr)
        return 2
    d1_prompt = (
        INSTR + "\n"
        f"人: {JA_ASKED}\n"
        f"答え: {JA_ANSWERED}\n"
        "動き:"
    )
    d1 = path_stack._generate(d1_prompt, path_stack.DANGO_TOKENS)
    d1c = path_stack.clip_completion(d1, ("人:", "答え:", "動き:"))
    print("=== D1 RAW ===")
    print(repr(d1))
    print("=== D1 CLIP ===")
    print(repr(d1c))
    print("D1 looks_japanese", looks(d1c or d1))

    d2_prompt = (
        INSTR + "\n\n"
        + FORM_EX + "\n"
        f"人: {JA_ASKED}\n"
        f"答え: {JA_ANSWERED}\n"
        "動き:"
    )
    d2 = path_stack._generate(d2_prompt, path_stack.DANGO_TOKENS)
    d2c = path_stack.clip_completion(d2, ("人:", "答え:", "動き:"))
    print("=== D2 RAW ===")
    print(repr(d2))
    print("=== D2 CLIP ===")
    print(repr(d2c))
    print("D2 looks_japanese", looks(d2c or d2))
    print("D2 exemplar_copied", path_stack.exemplar_copied((d2c or d2).strip()))
    print("D2 form_echo", (d2c or "").strip() == "剥がれた底を縫い直す")

    d3 = path_stack._generate(D3_STEM, path_stack.DANGO_TOKENS)
    print("=== D3 RAW ===")
    print(repr(d3))
    print("D3 looks_japanese", looks(d3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
