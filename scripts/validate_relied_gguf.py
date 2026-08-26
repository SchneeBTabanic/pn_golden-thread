#!/usr/bin/env python3
"""4b first fruit: needle through the hooked server, GGUF substrate.

Compares RELIED mass on the needle span for the 4a profiled heads versus
an equal number of control heads not in the profile. Transfer if the
profiled mass is greater. Flash attention must be off.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import model  # noqa: E402
import relied  # noqa: E402

HAY = (
    "The haystack is ordinary prose about orchards in winter. "
    "Trees stand without leaves. Snow covers the ground. "
)
NEEDLE = "The special retrieval code is ALPHA-PLACED-SEVEN-NINE."
ASK = "What is the special retrieval code? Copy it exactly."
GGUF = (os.environ.get("MODEL") or os.environ.get("GT_GGUF") or "").strip()
if not GGUF:
    sys.exit("Set MODEL or GT_GGUF to a .gguf path")
N_LAYER = 40
N_HEAD = 32


def build_prompt():
    hay = HAY * 8
    cut = len(hay) // 2
    return hay[:cut] + " " + NEEDLE + " " + hay[cut:] + "\n" + ASK


def find_span(tokens, needle_tokens):
    n = len(needle_tokens)
    for i in range(len(tokens) - n + 1):
        if tokens[i:i + n] == needle_tokens:
            return i, i + n
    if n > 2:
        inner = needle_tokens[1:]
        m = len(inner)
        for i in range(len(tokens) - m + 1):
            if tokens[i:i + m] == inner:
                return i, i + m
    return None, None


def run_one(prompt, heads, start, end, n_predict=24):
    payload = {
        "prompt": prompt,
        "n_predict": n_predict,
        "temperature": 0,
        "top_p": 1.0,
        "seed": 0,
        "cache_prompt": False,
        "gt_relied": {
            "heads": heads,
            "spans": [{"id": "needle", "start": start, "end": end}],
        },
    }
    return model.completion_raw(payload)


def main():
    if not model.health() or model.backend() != "llama":
        print("REFUSED — llama-server is not answering", file=sys.stderr)
        return 2
    prof = relied.load_profile(GGUF)
    if prof is None or not prof["heads"]:
        print("REFUSED — no profile for this GGUF", file=sys.stderr)
        return 2
    prompt = build_prompt()
    tokens = model.tokenize(prompt, add_special=False)
    needle_toks = model.tokenize(NEEDLE, add_special=False)
    start, end = find_span(tokens, needle_toks)
    if start is None:
        print("REFUSED — needle tokens not in prompt", file=sys.stderr)
        return 2
    profiled = [[int(a), int(b)] for a, b in prof["heads"]]
    control = relied.control_heads(profiled, N_LAYER, N_HEAD, len(profiled))
    if len(control) < len(profiled):
        print("REFUSED — could not form a control set", file=sys.stderr)
        return 2
    print("prompt_tokens", len(tokens), "needle", start, end, file=sys.stderr)
    print("running profiled heads", len(profiled), file=sys.stderr)
    rp = run_one(prompt, profiled, start, end)
    print("running control heads", len(control), file=sys.stderr)
    rc = run_one(prompt, control, start, end)
    fp = (relied.parse_gt_relied(rp) or {}).get("needle")
    fc = (relied.parse_gt_relied(rc) or {}).get("needle")
    out = {
        "profiled_fraction": fp,
        "control_fraction": fc,
        "profiled_n_steps": rp.get("gt_relied_n_steps"),
        "control_n_steps": rc.get("gt_relied_n_steps"),
        "profiled_saw_softmax": rp.get("gt_relied_saw_softmax"),
        "control_saw_softmax": rc.get("gt_relied_saw_softmax"),
        "profiled_n_heads": rp.get("gt_relied_n_heads"),
        "control_n_heads": rc.get("gt_relied_n_heads"),
        "needle_span": [start, end],
        "n_prompt_tokens": len(tokens),
        "profiled_content": (rp.get("content") or "")[:240],
        "control_content": (rc.get("content") or "")[:240],
        "heads_profiled": profiled,
        "heads_control": control,
    }
    if fp is None or fc is None:
        out["verdict"] = "hook-silent"
    elif not rp.get("gt_relied_saw_softmax"):
        out["verdict"] = "no-softmax-flash-attn-on"
    elif fp > fc:
        out["verdict"] = "transfer"
    else:
        out["verdict"] = "non-transfer"
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
