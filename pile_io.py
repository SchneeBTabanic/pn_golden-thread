"""
pile_io.py — talk to gForth scribe by subprocess; read a pile by extent.

Never import the Forth, never share a parser with the writer (Charter §3.5).
The writer is pn_gf-scribe-wb keep; this file learns the grammar from
documents and from piles that keep actually minted.

Grammar:
    @@ @formed:<utime> @extent:<bytes> @key:value ...
    <body, exactly @extent: bytes>
    <one newline, not counted in extent>
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GF_DIR = os.path.normpath(os.path.join(HERE, "..", "pn_gf-scribe-wb"))
SEAM = os.path.join(HERE, "pn-runtime-seam.fs")
GFORTH = os.environ.get("GT_GFORTH", "gforth")
LEAVES = ("pn-keep.fs", "pn-gread.fs", "pn-gindex.fs")
KEPT_PREFIX = "pn-scribe: KEPT "


class PileError(RuntimeError):
    pass


def seam_path():
    return os.environ.get("GT_SEAM", SEAM)


def gf_dir():
    return os.environ.get("GT_GF_SCRIBE", GF_DIR)


JOINER = "\n\n"


def parse_tags(header):
    """[(key, val), ...] from a gForth header line. No regex."""
    if not header.startswith("@@ "):
        return None
    rest = header[3:].lstrip()
    if rest.startswith("#"):
        raise PileError(
            "python-scribe header — this runtime writes gForth piles only")
    tags = []
    while rest.startswith("@"):
        rest = rest[1:]
        colon = rest.find(":")
        if colon <= 0:
            break
        key = rest[:colon]
        rest = rest[colon + 1:]
        i = 0
        while i < len(rest) and rest[i] not in " \t":
            i += 1
        tags.append((key, rest[:i]))
        rest = rest[i:].lstrip()
    return tags


def tag_map(tags):
    d = {}
    for k, v in tags:
        d[k] = v
    return d


def parse_pile(text):
    """Walk by @extent: bytes. Returns (genesis, blocks, short_by)."""
    raw = text.encode("utf-8") if isinstance(text, str) else text
    blocks = []
    genesis = ""
    short_by = 0
    pos = 0
    n = len(raw)
    while pos < n:
        if not raw.startswith(b"@@ ", pos):
            raise PileError(
                f"expected a header at byte {pos} and there is none. "
                f"SHORT by structure.")
        nl = raw.find(b"\n", pos)
        if nl < 0:
            raise PileError(f"header at byte {pos} never ends")
        header = raw[pos:nl].decode("utf-8")
        tags = parse_tags(header)
        if tags is None:
            raise PileError(f"unreadable header at byte {pos}")
        tmap = tag_map(tags)
        ext_s = tmap.get("extent", "")
        if not ext_s or ext_s[0] == "?":
            raise PileError(
                f"block at byte {pos} — UNRECORDED extent; body never finished")
        try:
            extent = int(ext_s)
        except ValueError:
            raise PileError(
                f"block at byte {pos} — extent {ext_s!r} is not a number")
        body_start = nl + 1
        if body_start + extent > n:
            short_by += 1
            raise PileError(
                f"block at byte {pos} declared {extent} — SHORT: extent runs "
                f"past the end of the file")
        body_raw = raw[body_start:body_start + extent]
        next_pos = body_start + extent
        if next_pos < n:
            if raw[next_pos:next_pos + 1] == b"\n":
                next_pos += 1
            else:
                short_by += 1
                raise PileError(
                    f"block at byte {pos} — no separator newline after body")
        formed = tmap.get("formed", "")
        if not genesis and tmap.get("genesis"):
            genesis = tmap["genesis"]
        try:
            body = body_raw.decode("utf-8")
        except UnicodeDecodeError as e:
            raise PileError(f"block at byte {pos} — body is not utf-8 ({e})")
        blocks.append({
            "id": str(pos),
            "offset": pos,
            "formed": formed,
            "ts": formed,
            "extent": extent,
            "tags": tags,
            "tagmap": tmap,
            "body": body,
            "header": header,
        })
        pos = next_pos
    return genesis, blocks, short_by


def load_pile(path):
    if not os.path.exists(path):
        return "", []
    with open(path, "rb") as f:
        raw = f.read()
    genesis, blocks, _short = parse_pile(raw)
    return genesis, blocks


def _parse_kept(blob):
    for line in (blob or "").splitlines():
        s = line.strip()
        if s.startswith(KEPT_PREFIX):
            token = s[len(KEPT_PREFIX):].strip()
            if not token or token.startswith("UNLINKABLE"):
                raise PileError(
                    "mint KEPT line named the pile UNLINKABLE — no substitute")
            if token.count("#") != 1 or "/" not in token.split("#", 1)[1]:
                raise PileError(
                    f"mint KEPT line malformed: {token!r}")
            return token
    raise PileError("mint KEPT line absent — never guessing an id")


def _gforth(word, argv, stdin_text=None, close_stdin=False):
    seam = seam_path()
    leaves_dir = gf_dir()
    if not os.path.isfile(seam):
        raise PileError(f"seam missing at {seam}. Set GT_SEAM.")
    if not os.path.isdir(leaves_dir):
        raise PileError(
            f"gForth scribe missing at {leaves_dir}. Set GT_GF_SCRIBE.")
    cmd = [GFORTH]
    for leaf in LEAVES:
        cmd.append(leaf)
    cmd.extend([seam, "-e", word + " bye", "--"])
    cmd.extend(argv)
    kw = {
        "cwd": leaves_dir,
        "text": True,
        "capture_output": True,
    }
    if close_stdin:
        kw["stdin"] = subprocess.DEVNULL
    else:
        kw["input"] = stdin_text if stdin_text is not None else ""
    try:
        proc = subprocess.run(cmd, **kw)
    except FileNotFoundError:
        raise PileError(
            f"{GFORTH} is not on PATH. gForth 0.7.3 is required.")
    return proc


def _forward_notes(stderr):
    for line in (stderr or "").splitlines():
        if line.startswith("pn-scribe:"):
            # KEPT is for the Python seam to parse, not a clock line.
            if line.startswith(KEPT_PREFIX):
                continue
            sys.stderr.write(line + "\n")


def capture_append(pile, body, tags, source="runtime"):
    """Mint one block via keep. Returns (three-part-name, genesis)."""
    del source  # tags already carry source; Forth keep has no --source
    parent = os.path.dirname(os.path.abspath(pile))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    parts = []
    for key, val in tags:
        if " " in key or " " in val:
            raise PileError(
                f"tag {key}:{val} contains a space — a header is one line. "
                f"Refusing to write.")
        parts.append("@" + key + ":" + val)
    tagstr = " ".join(parts)
    if not tagstr:
        raise PileError("no readable @key:value in the tags")
    text = body if (body or "").endswith("\n") else (body or "") + "\n"
    proc = _gforth("keep-stdin", [pile, tagstr], stdin_text=text)
    _forward_notes(proc.stderr)
    _forward_notes(proc.stdout)
    blob = (proc.stderr or "") + "\n" + (proc.stdout or "")
    if proc.returncode != 0:
        reason = (proc.stderr or proc.stdout or "").strip() or "no output"
        raise PileError(f"gForth keep refused ({proc.returncode}): {reason}")
    token = _parse_kept(blob)
    genesis = token.split("#", 1)[0]
    return token, genesis


def export_selector(pile, selector):
    """Bare bodies of blocks matching key:value, joined. Forth export-bare."""
    if ":" not in selector or selector.startswith(":"):
        raise PileError(
            f"{selector!r} is not key:value. Name a gather "
            f"(topic:turn, act:place-a-file) or use /shape alone.")
    proc = _gforth(
        "export-bare", [pile, selector, JOINER], close_stdin=True)
    _forward_notes(proc.stderr)
    if proc.returncode != 0:
        raise PileError(
            f"gForth export {selector} failed: "
            f"{(proc.stderr or proc.stdout or '').strip() or 'no output'}")
    text = (proc.stdout or "").strip()
    if not text:
        raise PileError(
            f"gForth export {selector} produced nothing. "
            f"No block carries that tag, or the export was empty.")
    return text


def toc_by(pile, key):
    proc = _gforth("toc-by", [pile, key], close_stdin=True)
    _forward_notes(proc.stderr)
    if proc.returncode != 0:
        raise PileError(
            f"gForth toc-by {key} failed: "
            f"{(proc.stderr or proc.stdout or '').strip() or 'no output'}")
    return (proc.stdout or "").rstrip()


def keys_of(pile):
    proc = _gforth("keys-of", [pile], close_stdin=True)
    _forward_notes(proc.stderr)
    if proc.returncode != 0:
        raise PileError(
            f"gForth keys-of failed: "
            f"{(proc.stderr or proc.stdout or '').strip() or 'no output'}")
    return (proc.stdout or "").rstrip()
