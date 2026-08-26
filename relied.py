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
ASKED_SPAN = "asked"
REACH_NOTE = (
    "(retrieval-head attention mass on placed spans; not faithfulness)"
)

_sha_cache = {}

# C2: per-token series. Hook is cut-ignorant. Segmentation is Python, after
# the tape cuts. Masses are integers at SERIES_SCALE. Additive: a pre-C2
# hook still carries the old fraction field.
SERIES_SCALE = 10000
NO_SERIES = "RELIED: hook answered without a per-token series"
SERIES_UNWALKABLE = "RELIED: series bytes do not account for the generation"
SERIES_RAGGED = "RELIED: series lengths disagree — refusing a ragged curve"
SERIES_BAD_ID = "RELIED: span id carries a space — refusing to write a series line"

# C3: boundary split. Standing calibration from the needle benchmark.
STRONG_MARK = 0.33
HUM_MARK = 0.05
UNDERSIDE_NOTE = "(retrieval-head attention on the live line; not relevance)"
NO_SPLIT = "UNDERSIDE: series does not account for the generation — refusing to split"
NO_CUT = "UNDERSIDE: no cut this turn — nothing to split"
CURVE_NO_PROFILES = "PROFILES: none — the split was refused this turn"


def parse_series(resp):
    """(series, note). None plus a named note when the hook did not speak it."""
    if not isinstance(resp, dict):
        return None, NO_SERIES
    raw = resp.get("gt_relied_series")
    if not isinstance(raw, dict):
        return None, NO_SERIES
    blens = raw.get("bytes")
    spans = raw.get("spans")
    if not isinstance(blens, list) or not isinstance(spans, dict) or not spans:
        return None, NO_SERIES
    n = len(blens)
    for name, vals in spans.items():
        if not isinstance(vals, list) or len(vals) != n:
            return None, SERIES_RAGGED
    scale = raw.get("scale")
    if not isinstance(scale, int) or scale <= 0:
        return None, NO_SERIES
    prefix = raw.get("prefix_bytes", 0)
    if not isinstance(prefix, int) or prefix < 0:
        return None, NO_SERIES
    return {
        "scale": scale,
        "prefix_bytes": prefix,
        "bytes": [int(x) for x in blens],
        "spans": {k: [int(v) for v in vals] for k, vals in spans.items()},
    }, ""


def series_accounts_for(series, generated_bytes):
    """True when prefix + the step bytes equal the generation exactly."""
    if not series:
        return False
    return (int(series.get("prefix_bytes") or 0)
            + sum(series.get("bytes") or [])) == int(generated_bytes)


def series_total_bytes(series):
    if not series:
        return 0
    return sum(series.get("bytes") or [])


def series_body(series):
    """SERIES section of the sibling block. Plain integers."""
    if not series:
        return ""
    scale = int(series.get("scale") or SERIES_SCALE)
    blens = series.get("bytes") or []
    lines = [
        "SERIES scale=" + str(scale) + " steps=" + str(len(blens))
        + " bytes=" + str(sum(blens))
        + " prefix=" + str(int(series.get("prefix_bytes") or 0)),
        "bytes " + " ".join(str(int(b)) for b in blens),
    ]
    for name in sorted(series.get("spans") or {}):
        if " " in name:
            raise ValueError(SERIES_BAD_ID + ": " + name)
        vals = series["spans"][name]
        lines.append("span " + name + " " + " ".join(str(int(v)) for v in vals))
    return "\n".join(lines)


def split_series(series, cut_byte, generated_bytes):
    """(profiles, note). Refuse rather than walk a series that does not reconcile."""
    if not series:
        return None, NO_SERIES
    if cut_byte is None:
        return None, NO_CUT
    if not series_accounts_for(series, generated_bytes):
        return None, NO_SPLIT
    names = sorted(series.get("spans") or {})
    blens = series.get("bytes") or []
    face = {n: [] for n in names}
    under = {n: [] for n in names}
    boundary = {}
    boundary_index = None
    pos = int(series.get("prefix_bytes") or 0)
    cut = int(cut_byte)
    for i, blen in enumerate(blens):
        start, end = pos, pos + int(blen)
        pos = end
        if end <= cut:
            seat = face
        elif start >= cut:
            seat = under
        else:
            boundary_index = i
            for n in names:
                boundary[n] = series["spans"][n][i]
            continue
        for n in names:
            seat[n].append(series["spans"][n][i])
    return {
        "scale": int(series.get("scale") or SERIES_SCALE),
        "face": face,
        "underside": under,
        "boundary": boundary,
        "boundary_index": boundary_index,
        "boundary_count": 0 if boundary_index is None else 1,
        "unmeasured_prefix_bytes": int(series.get("prefix_bytes") or 0),
    }, ""


def _mean(vals, scale):
    if not vals:
        return None
    return (sum(vals) / len(vals)) / float(scale)


def count_returns(vals, scale, mark=STRONG_MARK):
    """Rising crossings of the strong mark. A run of high steps counts once."""
    n = 0
    was_above = False
    for v in vals or []:
        above = (v / float(scale)) >= mark
        if above and not was_above:
            n += 1
        was_above = above
    return n


def underside_clock(profiles, span):
    """The UNDERSIDE line. Named absence where a side had no steps."""
    if not profiles:
        return ""
    scale = profiles["scale"]
    mf = _mean(profiles["face"].get(span) or [], scale)
    mu = _mean(profiles["underside"].get(span) or [], scale)
    fs = "(none)" if mf is None else format_frac(mf)
    us = "(none)" if mu is None else format_frac(mu)
    line = ("UNDERSIDE: " + str(span) + "-mass \u03bcface " + fs
            + " \u2192 \u03bcsequel " + us
            + " \u00b7 returns: "
            + str(count_returns(profiles["underside"].get(span) or [], scale)))
    if profiles["boundary_count"]:
        line += " \u00b7 boundary: 1 step unassigned"
    return line + "   " + UNDERSIDE_NOTE


def profiles_body(profiles):
    """PROFILES section of the sibling block. Counts always, zero included."""
    if not profiles:
        return ""
    scale = profiles["scale"]
    lines = ["PROFILES boundary=" + str(profiles["boundary_count"])
             + " prefix_unmeasured=" + str(profiles["unmeasured_prefix_bytes"])]
    for seat in ("face", "underside"):
        for name in sorted(profiles[seat]):
            vals = profiles[seat][name]
            m = _mean(vals, scale)
            lines.append(seat + " " + name + " steps=" + str(len(vals))
                         + " mean=" + ("none" if m is None else format_frac(m)))
    for name in sorted(profiles["boundary"]):
        lines.append("boundary " + name + " " + str(profiles["boundary"][name]))
    return "\n".join(lines)


def bin_frac(mean):
    """Coarse seat for a header. Named absence, never a bin invented for None."""
    if mean is None:
        return "none"
    if float(mean) >= STRONG_MARK:
        return "strong"
    if float(mean) <= HUM_MARK:
        return "hum"
    return "between"


def curve_bins(profiles):
    """[(seat, span, bin)] for header disclosure."""
    if not profiles:
        return []
    scale = profiles["scale"]
    out = []
    for seat in ("face", "underside"):
        for name in sorted(profiles[seat]):
            out.append((seat, name, bin_frac(_mean(profiles[seat][name], scale))))
    return out


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


NO_READING_FOR = "no reading for"
STOP_NOTE = "(what ended the completion; not a judgement of it)"
STOP_NO_REPLY = "STOPPED: no completion this turn — nothing to have ended"
STOP_UNSAID = (
    "STOPPED: the reply carried no stop_type — this build did not "
    "say, and nothing here will guess"
)


def _tokens_said(resp):
    n = resp.get("tokens_predicted")
    if isinstance(n, bool) or not isinstance(n, int):
        return "token count not said"
    return "token " + str(n)


def stopped_clock(resp):
    """Named line for what ended a completion. Read, never derived."""
    if not isinstance(resp, dict):
        return STOP_NO_REPLY
    if "stop_type" not in resp:
        return STOP_UNSAID
    kind = resp.get("stop_type")
    at = _tokens_said(resp)
    if kind == "eos":
        body = "eos at " + at
    elif kind == "limit":
        body = "cap reached at " + at
    elif kind == "word":
        word = resp.get("stopping_word")
        if not isinstance(word, str) or not word:
            body = "stop-string at " + at + " (which string was not said)"
        else:
            body = "stop-string " + repr(word) + " at " + at
    else:
        body = str(kind) + " at " + at + " (stop_type not recognised here)"
    return "STOPPED: " + body + "   " + STOP_NOTE


def unaccounted_spans(resp, names):
    """Named pieces the hook returned no reading for.

    Empty when the hook did not speak at all: that absence already has
    a name (NO_HOOK). Listing every span as unread there would bury it.
    """
    got = parse_gt_relied(resp)
    if got is None:
        return []
    return [n for n in (names or []) if n not in got]


def masses_clock(pairs, unaccounted=()):
    """RELIED clock when spans were placed and the hook answered.

    `unaccounted` names pieces that were placed and came back with no
    reading. They are stated, never dropped.
    """
    missing = [str(n) for n in (unaccounted or [])]
    if not pairs:
        if missing:
            return (
                "RELIED: " + NO_READING_FOR + ": " + ", ".join(missing)
                + "   " + REACH_NOTE
            )
        return NONE_PLACED
    bits = []
    for name, frac in pairs:
        bits.append(str(name) + " " + format_frac(frac))
    line = "RELIED: " + " · ".join(bits)
    if missing:
        line += " · " + NO_READING_FOR + ": " + ", ".join(missing)
    return line + "   " + REACH_NOTE


def clock(backend, model_path, masses=None, placed=False,
          unaccounted=()):
    """Named RELIED line. Never a mass invented. Never all-heads."""
    if backend != "llama":
        return costume_line(backend)
    prof = load_profile(model_path)
    if prof is None:
        return UNPROFILED
    if not prof["heads"]:
        return NO_HEADS
    if masses or unaccounted:
        return masses_clock(masses, unaccounted)
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


def token_range_last(full, piece, tokenize_fn):
    """Like token_range, but the LAST occurrence.

    C1: the live mouth line sits last in the face window. A placed file
    that quotes the question back would otherwise capture the span.
    """
    if not piece:
        return None
    idx = (full or "").rfind(piece)
    if idx < 0:
        return None
    start = len(tokenize_fn((full or "")[:idx]))
    end = len(tokenize_fn((full or "")[:idx + len(piece)]))
    if end < start:
        return None
    return start, end


def spans_for_hook(full_prompt, named_pieces, tokenize_fn, last_ids=()):
    """named_pieces: [(id, text), ...]. Only pieces found in the prompt.

    Ids in last_ids are located at their LAST occurrence.
    """
    out = []
    for sid, text in named_pieces or []:
        if sid in (last_ids or ()):
            rng = token_range_last(full_prompt, text, tokenize_fn)
        else:
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
