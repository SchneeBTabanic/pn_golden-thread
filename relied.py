"""
relied.py — load a retrieval-head profile. Never compute heads at runtime.

A missing profile is a named refusal. An empty heads list is a named
refusal. There is no fallback to all-heads.

RELIED says where attention mass went, not whether the answer is
faithful or true. (Masses themselves wait on the server hook.)
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HEADS_DIR = os.path.join(HERE, "law", "heads")

UNPROFILED = "RELIED: unprofiled model — run the profiler"
NO_HEADS = "RELIED: profile loaded — no retrieval heads recorded"
NO_HOOK = "RELIED: profile loaded — server hook not built"
NONE_PLACED = "RELIED: none placed"
REACH_NOTE = (
    "(retrieval-head attention mass on placed spans; not faithfulness)"
)

_sha_cache = {}


def heads_dir():
    return os.environ.get("GT_HEADS_DIR", DEFAULT_HEADS_DIR)


def file_sha256(path):
    """Full sha256 of a file. Cached by path, size, mtime."""
    if not path or not os.path.isfile(path):
        return ""
    st = os.stat(path)
    key = (os.path.abspath(path), st.st_size, int(st.st_mtime))
    hit = _sha_cache.get(key)
    if hit:
        return hit
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    digest = h.hexdigest()
    _sha_cache[key] = digest
    return digest


def _as_head_pair(item):
    if not isinstance(item, (list, tuple)) or len(item) != 2:
        return None
    try:
        layer = int(item[0])
        head = int(item[1])
    except (TypeError, ValueError):
        return None
    if layer < 0 or head < 0:
        return None
    return [layer, head]


def parse_profile(obj):
    """Return a profile dict or None if the JSON is not wearable."""
    if not isinstance(obj, dict):
        return None
    sha = obj.get("sha256")
    heads_raw = obj.get("heads")
    method = obj.get("method")
    date = obj.get("date")
    model_path = obj.get("model_path")
    if not sha or not method or not date:
        return None
    if not isinstance(heads_raw, list):
        return None
    heads = []
    for item in heads_raw:
        pair = _as_head_pair(item)
        if pair is None:
            return None
        heads.append(pair)
    return {
        "model_path": model_path or "",
        "sha256": str(sha),
        "heads": heads,
        "method": str(method),
        "date": str(date),
    }


def load_profile(model_path):
    """Profile whose sha256 matches the bytes of model_path. Else None.

    Never invents heads. A swapped file cannot wear another sha's profile.
    """
    digest = file_sha256(model_path)
    if not digest:
        return None
    folder = heads_dir()
    if not os.path.isdir(folder):
        return None
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(folder, name)
        try:
            obj = json.loads(open(path, encoding="utf-8").read())
        except (OSError, ValueError):
            continue
        prof = parse_profile(obj)
        if prof is None:
            continue
        if prof["sha256"] == digest:
            return prof
    return None


def costume_line(backend):
    name = backend or "none"
    return (
        "RELIED binds on llama-server. This backend is "
        + name
        + ". Computing it here would be a costume. Refusing."
    )


def format_frac(x):
    return "%.2f" % float(x)


def relied_tag_value(name, frac):
    """Space-free tag value: traveling-name-0.71. Slashes in the name stay."""
    return str(name) + "-" + format_frac(frac)


def masses_clock(pairs):
    """RELIED clock when spans were placed and the hook answered."""
    if not pairs:
        return NONE_PLACED
    bits = []
    for name, frac in pairs:
        bits.append(str(name) + " " + format_frac(frac))
    return "RELIED: " + " · ".join(bits) + "   " + REACH_NOTE


def clock(backend, model_path, masses=None, placed=False):
    """Named RELIED line. Never a mass invented. Never all-heads."""
    if backend != "llama":
        return costume_line(backend)
    prof = load_profile(model_path)
    if prof is None:
        return UNPROFILED
    if not prof["heads"]:
        return NO_HEADS
    if masses:
        return masses_clock(masses)
    if not placed:
        return NONE_PLACED
    return NO_HOOK


def token_range(full, piece, tokenize_fn):
    """Token [start, end) covering `piece` inside `full`, via prefix lengths."""
    if not piece:
        return None
    idx = (full or "").find(piece)
    if idx < 0:
        return None
    start = len(tokenize_fn((full or "")[:idx]))
    end = len(tokenize_fn((full or "")[:idx + len(piece)]))
    if end < start:
        return None
    return start, end


def spans_for_hook(full_prompt, named_pieces, tokenize_fn):
    """named_pieces: [(id, text), ...]. Only pieces found in the prompt."""
    out = []
    for sid, text in named_pieces or []:
        rng = token_range(full_prompt, text, tokenize_fn)
        if rng is None:
            continue
        a, b = rng
        out.append({"id": sid, "start": int(a), "end": int(b)})
    return out


def parse_gt_relied(resp):
    """Take gt_relied from a completion JSON. None if the hook did not speak."""
    if not isinstance(resp, dict):
        return None
    if "gt_relied" not in resp:
        return None
    got = resp.get("gt_relied")
    if not isinstance(got, dict):
        return None
    return got


def fraction_mean(mass_sum, n_heads, n_steps):
    """Mean over profiled heads and decode steps of span mass."""
    n_heads = int(n_heads or 0)
    n_steps = int(n_steps or 0)
    if n_heads <= 0 or n_steps <= 0:
        return 0.0
    return float(mass_sum) / float(n_heads * n_steps)


def control_heads(profiled, n_layer, n_head, n):
    """n heads not in the profile. Never the profiled set. Never all-heads."""
    taken = set()
    for pair in profiled or []:
        taken.add((int(pair[0]), int(pair[1])))
    out = []
    for layer in range(int(n_layer)):
        for head in range(int(n_head)):
            if (layer, head) in taken:
                continue
            out.append([layer, head])
            if len(out) >= int(n):
                return out
    return out
