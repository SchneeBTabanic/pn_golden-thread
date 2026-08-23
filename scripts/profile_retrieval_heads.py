#!/usr/bin/env python3
"""Offline 4a profiler: Needle-in-a-Haystack copy-score (Wu et al. 2024).

Adapts nightdessert/Retrieval_Head to emit one JSON per checkpoint:

    {model_path, sha256, heads:[[layer,head],...], method, date}

Loaded at runtime. Never computed on a turn. Missing profile → named
refusal. This script never writes an all-heads list.

Needs PyTorch + transformers on the HF weights. The JSON is pinned to
the GGUF the runtime actually loads (--gguf), so a swapped file cannot
wear this profile.

    python3 scripts/profile_retrieval_heads.py \\
        --hf /mnt/data/models/granite-3.3-8b-hf \\
        --gguf /mnt/data/models/granite-3.3-8b-Q4_K_M.gguf \\
        --out law/heads/
"""
import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import relied  # noqa: E402

HAY = (
    "The haystack is ordinary prose about orchards in winter. "
    "Trees stand without leaves. Snow covers the ground. "
)
NEEDLE = "The special retrieval code is ALPHA-PLACED-SEVEN-NINE."
ASK = "What is the special retrieval code? Copy it exactly."
THRESHOLD = 1.0


def _die(msg):
    print("REFUSED — " + msg, file=sys.stderr)
    return 2


def detect(hf_path, n_ctx, n_trials, device):
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        return None, "pytorch/transformers missing — cannot run NIAH copy-score"

    tok = AutoTokenizer.from_pretrained(hf_path, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        hf_path,
        dtype=torch.bfloat16,
        attn_implementation="eager",
        device_map=None,
        local_files_only=True,
    )
    model.to(device)
    model.eval()
    n_layer = int(model.config.num_hidden_layers)
    n_head = int(model.config.num_attention_heads)
    hits = [[0.0 for _ in range(n_head)] for _ in range(n_layer)]
    denom = 0

    hay_budget = max(16, n_ctx - 48)
    hay_ids = tok(HAY * 40, add_special_tokens=False)["input_ids"][:hay_budget]
    needle_ids = tok(NEEDLE, add_special_tokens=False)["input_ids"]
    ask_ids = tok("\n" + ASK, add_special_tokens=False)["input_ids"]
    if not needle_ids or not hay_ids:
        return None, "tokenizer produced empty hay or needle ids"
    depths = [0.25, 0.5, 0.75][:n_trials]
    for depth in depths:
        cut = int(len(hay_ids) * depth)
        if cut < 0:
            cut = 0
        if cut > len(hay_ids):
            cut = len(hay_ids)
        seq = hay_ids[:cut] + needle_ids + hay_ids[cut:] + ask_ids
        needle_pos = list(range(cut, cut + len(needle_ids)))
        needle_set = set(needle_pos)
        ids = torch.tensor([seq], device=device)
        with torch.no_grad():
            out = model(
                input_ids=ids, output_attentions=True, use_cache=False)
        for layer, attn in enumerate(out.attentions):
            last = attn[0, :, -1, :]
            argmax = last.argmax(dim=-1)
            for h in range(n_head):
                pos = int(argmax[h].item())
                if pos in needle_set:
                    hits[layer][h] += 1.0
        denom += 1
        del out, ids
    if denom == 0:
        return None, "needle tokens were not found in the prompt — nothing scored"
    heads = []
    scores = {}
    for layer in range(n_layer):
        for h in range(n_head):
            score = hits[layer][h] / denom
            if score >= THRESHOLD:
                heads.append([layer, h])
            scores["%d-%d" % (layer, h)] = round(score, 4)
    return {
        "heads": heads,
        "n_layer": n_layer,
        "n_head": n_head,
        "n_trials": denom,
        "threshold": THRESHOLD,
        "scores_nonzero": {k: v for k, v in scores.items() if v > 0},
    }, ""


def main(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hf", required=True, help="HF checkpoint directory")
    p.add_argument("--gguf", required=True, help="runtime GGUF this profile pins")
    p.add_argument("--out", default=os.path.join(HERE, "law", "heads"))
    p.add_argument("--ctx", type=int, default=128)
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--device", default="cpu")
    args = p.parse_args(argv)

    if not os.path.isdir(args.hf):
        return _die("HF path is not a directory: " + args.hf)
    if not os.path.isfile(args.gguf):
        return _die("GGUF is not a file: " + args.gguf)

    got, err = detect(args.hf, args.ctx, args.trials, args.device)
    if err:
        return _die(err)

    digest = relied.file_sha256(args.gguf)
    if not digest:
        return _die("could not hash GGUF")
    os.makedirs(args.out, exist_ok=True)
    rec = {
        "model_path": os.path.abspath(args.gguf),
        "sha256": digest,
        "heads": got["heads"],
        "method": (
            "niah-copy-score nightdessert/Retrieval_Head adapted; "
            "eager attention last-query argmax onto needle span; "
            "threshold %s; trials %s; ctx %s; measured on HF %s"
            % (got["threshold"], got["n_trials"], args.ctx, args.hf)
        ),
        "date": datetime.date.today().isoformat(),
    }
    out_path = os.path.join(args.out, digest + ".json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2)
        f.write("\n")
    print("wrote", out_path)
    print("heads", len(rec["heads"]), rec["heads"][:20])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
