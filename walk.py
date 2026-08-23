"""
walk.py — the model walks the compact register; the clerk writes.

The model must not invent keys. The clerk refuses a space, an unknown
key, a grouping value off the closed list, and seats the mouth owns
(act, source — those are facts, not meaning).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REGISTER = os.path.join(HERE, "tag_register.json")
LEGACY_REGISTER = os.path.join(HERE, "tag_register.txt")

MOUTH_OWNED = ("act", "source", "captured")


def load_register(path=None):
    """Return {key: (kind, [values] or None)}. Prefers the JSON register."""
    import json
    p = path or os.environ.get("GT_TAG_REGISTER", DEFAULT_REGISTER)
    if p.endswith(".json"):
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        out = {}
        for key, spec in (data.get("keys") or {}).items():
            vals = spec.get("values")
            out[key] = (spec.get("kind") or "witness", vals)
        return out
    out = {}
    with open(p, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            key, kind, spec = parts[0], parts[1], parts[2]
            vals = None if spec == "*" else spec.split(",")
            out[key] = (kind, vals)
    return out


def load_register_full(path=None):
    """The JSON object, including English meanings. Dango is not given this."""
    import json
    p = path or os.environ.get("GT_TAG_REGISTER", DEFAULT_REGISTER)
    if not p.endswith(".json"):
        p = DEFAULT_REGISTER
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def register_as_prompt(reg):
    lines = [
        "Walk every key. One line per key you fill:",
        "  @key:value",
        "Or: EMPTY key",
        "Do not invent a key. Values have no spaces (use hyphens).",
        "Grouping keys may only use the listed values.",
        "Meaning seats you may fill: path (if you see a toward), because,",
        "attests, awaits, rejected, dissolves, touched, part, name, refuses.",
        "touched may be executor, proxy, shape, sequel, schnee.",
        "Keys:",
    ]
    for key in sorted(reg):
        kind, vals = reg[key]
        if vals:
            lines.append(f"  @{key}: ({kind}) " + ",".join(vals))
        else:
            lines.append(f"  @{key}: ({kind}) free-hyphenated")
    return "\n".join(lines)


def parse_walk(text, reg):
    """Return (accepted [(k,v)], refused [reason], empties [key])."""
    accepted, refused, empties = [], [], []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.upper().startswith("EMPTY "):
            empties.append(line.split(None, 1)[1].strip().lstrip("@"))
            continue
        if not line.startswith("@"):
            continue
        rest = line[1:]
        if ":" not in rest:
            refused.append(f"no-colon {line}")
            continue
        key, val = rest.split(":", 1)
        key, val = key.strip(), val.strip()
        if not key or not val:
            refused.append(f"empty {line}")
            continue
        if " " in key or " " in val:
            refused.append(f"space {key}:{val}")
            continue
        if key in MOUTH_OWNED:
            refused.append(f"mouth-owned {key}")
            continue
        if key not in reg:
            refused.append(f"unknown {key}")
            continue
        kind, vals = reg[key]
        if vals is not None and val not in vals:
            refused.append(f"closed-class {key}:{val}")
            continue
        del kind
        accepted.append((key, val))
    return accepted, refused, empties


def walk_user_prompt(asked, answered, declared=""):
    parts = [
        "This turn:",
        f"asked: {asked}",
        f"answered: {answered}",
    ]
    if declared:
        parts.append(f"declared !path: {declared}")
    parts.append("Walk the keys now.")
    return "\n".join(parts)
