"""
path_stack.py — summoned Japanese → gloss → optional L2 display.

/walk only. Talk does not run this. Proposed tags are never a filing order.

  L1 Dango writes one Japanese sentence. It is not asked for English.
  gloss.py turns that into Leipzig English in Japanese order.
  If the turn already carries a written @act, L2 is skipped and the
  written tag is witnessed. Otherwise Granite 8B (the face) writes
  two tag lines from Japanese + gloss + the live-core tag sheet.
  Proposed tags are shown, not filed.

  off_gloss is a display (stems not in the gloss). It does not veto.
  Exemplar copy is an exact string match against L1 few-shot lines.

Python holds tag_register.json as a clerk list. Dango is Japanese-only.
Granite L2 and Granite look are handed the live core of TAGS-gforth.md
(researched meanings, not a menu). dango_l2_tags remains in this file
as the old English hop; run_stack does not call it.
The heuristic propose_from_* helpers stay for tests. They are not the last hop.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_MIDWIFE = os.path.abspath(os.path.join(HERE, "..", "ref", "ontology-midwife"))
DANGO_DIR = os.environ.get(
    "GT_DANGO",
    os.path.join(_MIDWIFE, "model", "dango-1.8b"))
GLOSS_PY = os.environ.get(
    "GT_GLOSS_PY",
    os.path.join(_MIDWIFE, "tagging-lab", "gloss.py"))
GLOSS_PYTHON = os.environ.get(
    "GT_GLOSS_PYTHON",
    os.path.join(_MIDWIFE, "tagging-lab", ".venv", "bin", "python"))
DANGO_TOKENS = int(os.environ.get("GT_DANGO_TOKENS", "80"))
DANGO_L2_TOKENS = int(os.environ.get("GT_DANGO_L2_TOKENS", "28"))
DANGO_ASK_TOKENS = int(os.environ.get("GT_DANGO_ASK_TOKENS", "256"))
DANGO_ANS_TOKENS = int(os.environ.get("GT_DANGO_ANS_TOKENS", "256"))
TAG_SHEET = os.path.normpath(os.path.join(
    HERE, "..", "pn_gf-scribe-wb", "TAGS-gforth.md"))


def tag_sheet_text():
    """Whole gForth sheet. Missing is named. Nothing is substituted."""
    path = os.environ.get("GT_TAG_SHEET", TAG_SHEET)
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return f"[TAG SHEET ABSENT at {path} ({e}). Nothing was substituted.]"
    if not (text or "").strip():
        return f"[TAG SHEET EMPTY at {path}. Nothing was substituted.]"
    return text


def tag_sheet_live_core():
    """Sections 1–2: act, path, named empties, closed vocab. Fits a 8B window."""
    text = tag_sheet_text()
    if text.startswith("[TAG SHEET ABSENT") or text.startswith("[TAG SHEET EMPTY"):
        return text
    mark = "\n## 3."
    i = text.find(mark)
    core = text[:i] if i > 0 else text
    path = os.environ.get("GT_TAG_SHEET", TAG_SHEET)
    return (
        "[TAG SHEET live core — " + path
        + ". Researched meanings, not a menu.]\n" + core
    )
# run.py is started with system python3; torch lives in this env.
DANGO_SITE = os.environ.get(
    "GT_DANGO_SITE",
    "/home/schnee/vessel-env/lib/python3.13/site-packages")

_NAMED_EMPTY = ("not-yet-discerned", "ruled-none")
# Longest first so away-from- wins over away- and from-.
_DIRECTIONS = (
    "away-from-", "out-of-", "back-to-", "towards-", "toward-",
    "into-", "onto-", "from-", "away-", "over-", "back-",
    "beyond-", "across-", "through-", "past-", "out-",
)
_THIN_STEMS = ("the", "a", "an")
# Closed Leipzig class. A tag that quotes these is marker leakage, not content.
# tag_validator.py: only closed grammatical classes gate hard.
_LEIPZIG_MARKERS = frozenset((
    "ACC", "NOM", "DAT", "TOP", "AUX", "SEQ", "PROG", "GEN", "LOC", "ABL",
    "COM", "NMLZ", "CASE", "ALL", "TERM", "RES", "PREP", "COMPL", "TRY",
    "BEN", "SFP", "ADV.P", "AUX.V",
))
# Narrow nominalisation: verb + one noun in these endings. The wide form
# (any such noun anywhere) is not shipped — a named object is a doing.
_NOM_ENDS = ("tion", "sion", "ment", "ance", "ence", "ity", "ness", "ure")
# Exact Japanese lines the old few-shot used. Guard remains; they are
# no longer in the prompt. Verbatim copy only.
L1_EXEMPLARS = (
    "空を鳥が渡っていく",
    "窓を開けて風を入れる",
)

_dango = {"tok": None, "model": None, "error": ""}


def dango_ready():
    return os.path.isdir(DANGO_DIR) and os.path.isfile(
        os.path.join(DANGO_DIR, "model.safetensors"))


def gloss_ready():
    return os.path.isfile(GLOSS_PY) and os.path.isfile(GLOSS_PYTHON)


def _load_dango():
    if _dango["model"] is not None:
        return True
    if _dango["error"]:
        return False
    if not dango_ready():
        _dango["error"] = "Dango weights missing at " + DANGO_DIR
        return False
    try:
        try:
            import torch
        except ImportError:
            if DANGO_SITE and DANGO_SITE not in sys.path:
                sys.path.insert(0, DANGO_SITE)
            import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(DANGO_DIR, trust_remote_code=True)
        mdl = AutoModelForCausalLM.from_pretrained(
            DANGO_DIR,
            dtype=torch.bfloat16,
            device_map="cpu",
            low_cpu_mem_usage=True,
        )
        mdl.eval()
        _dango["tok"] = tok
        _dango["model"] = mdl
        return True
    except Exception as e:
        _dango["error"] = f"Dango failed to load ({e})"
        return False


def _generate(prompt, max_new_tokens):
    if not _load_dango():
        raise RuntimeError(_dango["error"])
    import torch
    tok = _dango["tok"]
    mdl = _dango["model"]
    enc = tok(prompt, return_tensors="pt")
    enc.pop("token_type_ids", None)
    with torch.no_grad():
        out = mdl.generate(
            **enc,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tok.eos_token_id or tok.pad_token_id,
        )
    return tok.decode(
        out[0][enc["input_ids"].shape[1]:],
        skip_special_tokens=True).strip()


def first_sentence(text):
    """Keep the first Japanese or Latin sentence. Dango sometimes rambles."""
    s = (text or "").strip()
    if not s:
        return ""
    for sep in ("。", "．", "\n", ". "):
        i = s.find(sep)
        if i > 0:
            return s[:i].strip()
    return s


def looks_japanese(text):
    for ch in text or "":
        o = ord(ch)
        if 0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF:
            return True
    return False


def japanese_span(text):
    """Drop a leading Latin echo; keep from the first Japanese character."""
    start = None
    for i, ch in enumerate(text or ""):
        o = ord(ch)
        if 0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF:
            start = i
            break
    if start is None:
        return ""
    return (text or "")[start:].strip()


def budget_text(text, budget, tok):
    """Keep a prefix by token count. Returns (kept, n_tokens, n_cut).

    Character slicing is not a reading. A zero cut is named later, not silent.
    """
    raw = text or ""
    budget = int(budget)
    if budget < 0:
        budget = 0
    ids = tok.encode(raw, add_special_tokens=False)
    n = len(ids)
    if n <= budget:
        return raw, n, 0
    kept = tok.decode(ids[:budget], skip_special_tokens=True)
    return kept, n, n - budget


def l1_cut_note(asked_n, asked_cut, ans_n, ans_cut):
    """Always name the cut, including none."""
    if asked_cut == 0 and ans_cut == 0:
        return (
            "input: ASKED %d tokens kept whole; ANSWERED %d tokens kept whole; "
            "nothing cut" % (asked_n, ans_n)
        )
    return (
        "input: ASKED %d tokens kept %d (cut %d); "
        "ANSWERED %d tokens kept %d (cut %d)"
        % (asked_n, asked_n - asked_cut, asked_cut,
           ans_n, ans_n - ans_cut, ans_cut)
    )


def l1_instruction_prompt(asked, answered, tok):
    """Zero-shot Japanese instruction. No topic exemplars. Token-budgeted."""
    asked_k, an, acut = budget_text(asked, DANGO_ASK_TOKENS, tok)
    ans_k, bn, bcut = budget_text(answered, DANGO_ANS_TOKENS, tok)
    note = l1_cut_note(an, acut, bn, bcut)
    prompt = (
        "会話の動きを短い日本語の一文で書く。英語は書かない。\n"
        f"人: {asked_k}\n"
        f"答え: {ans_k}\n"
        "動き:"
    )
    return prompt, note


def clip_completion(text, stops):
    s = text or ""
    cut = len(s)
    for stop in stops:
        i = s.find(stop)
        if 0 < i < cut:
            cut = i
    return s[:cut].strip()


def dango_sequel_look(declared, sequel):
    """One short Japanese sentence of leftover speech against a declared path.

    A reading, not a tag, not a yes/no for Python to file on.
    Zero-shot so the sky-bird exemplars cannot be copied onto the tail.
    """
    declared = (declared or "").strip()[:200]
    sequel = first_sentence(sequel)[:400]
    prompt = (
        "残りの話が、人が示した道の上を動いているか、短い日本語の一文で書く。"
        "英語は書かない。\n"
        f"道: {declared}\n"
        f"残り: {sequel}\n"
        "動き:"
    )
    text = _generate(prompt, DANGO_TOKENS)
    return clip_completion(text, ("道:", "残り:", "動き:", "人:", "答え:"))


def dango_japanese(asked, answered):
    """One short Japanese sentence. Whole ASKED/ANSWERED, no topic exemplars."""
    if not _load_dango():
        raise RuntimeError(_dango["error"])
    prompt, note = l1_instruction_prompt(asked, answered, _dango["tok"])
    text = _generate(prompt, DANGO_TOKENS)
    jp = clip_completion(text, ("人:", "答え:", "動き:"))
    return jp, note


def content_stems(interlinear):
    """English content stems from a Leipzig line. POS labels stay out."""
    skip = {"補助記号", "空白"}
    out, seen = [], set()
    for piece in (interlinear or "").split():
        if piece in skip or piece.endswith("?"):
            continue
        if piece.isupper():
            continue
        for part in piece.replace(".", "-").split("-"):
            low = part.lower()
            if (not low or low in _THIN_STEMS or part.isupper()
                    or low in seen):
                continue
            seen.add(low)
            out.append(low)
    return out


def dango_l2_tags(japanese, gloss):
    """L2 English: two hyphenated tag lines. Gloss stems are the only words."""
    stems = content_stems(gloss)
    allowed = ", ".join(stems) if stems else "(none)"
    prompt = (
        "グロスに出た語だけ使う。無い語は書かない。タグ二行だけ。\n"
        "\n"
        "日本語: 空を鳥が渡っていく\n"
        "グロス: sky bird cross.over-SEQ-go\n"
        "使える語: sky, bird, cross, over, go\n"
        "@act:cross-over-go\n"
        "@path:toward-sky-bird\n"
        "\n"
        f"日本語: {japanese}\n"
        f"グロス: {gloss}\n"
        f"使える語: {allowed}\n"
        "@act:"
    )
    raw = "@act:" + _generate(prompt, DANGO_L2_TOKENS)
    return clip_completion(raw, ("日本語:", "グロス:", "人:", "使える語:"))


GRANITE_L2_SYSTEM = (
    "You write exactly two tag lines for this exchange.\n"
    "The Japanese sentence is the movement. The gloss is checkable English "
    "in Japanese order.\n"
    "Use the tag sheet's meanings. Do not walk every key.\n"
    "Hyphenate. No spaces.\n"
    "@act: is a verb-phrase that is still happening, not a finished moment.\n"
    "@path: starts with a direction word plus real words, or is "
    "not-yet-discerned or ruled-none.\n"
    "Prefer gloss stems. If you need a word the gloss lacks, put it on the "
    "tag line anyway and add a third line invented: those-words.\n"
    "If you cannot tell the path, @path:not-yet-discerned.\n"
)


def granite_l2_tags(japanese, gloss):
    """English @act/@path from the face model. Dango is not asked."""
    import model
    stems = content_stems(gloss)
    user = tag_sheet_live_core()
    user += "\n\n[JAPANESE]\n" + (japanese or "")
    user += "\n\n[GLOSS]\n" + (gloss or "")
    if stems:
        user += "\n\n[GLOSS STEMS — what the Japanese said]\n" + ", ".join(stems)
    return model.look(GRANITE_L2_SYSTEM, user)


def run_gloss(japanese):
    """Call the midwife glosser. Returns (interlinear, raw_stdout)."""
    if not gloss_ready():
        raise RuntimeError("gloss.py or its venv python is missing")
    proc = subprocess.run(
        [GLOSS_PYTHON, GLOSS_PY, japanese],
        text=True, capture_output=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError("gloss failed: " + (out.strip() or "no output"))
    inter = ""
    for ln in out.splitlines():
        s = ln.strip()
        if s.startswith("→") or s.startswith("->"):
            inter = s.lstrip("→").lstrip("->").strip()
    return inter, out


def hyphen(s):
    out = []
    for ch in (s or ""):
        if ch == " " or ch == "/" or ch == "_":
            out.append("-")
        else:
            out.append(ch)
    text = "".join(out)
    while "--" in text:
        text = text.replace("--", "-")
    return text.strip("-")


def _take_tag_value(s):
    """s is the text after 'act:' or 'path:'. Stop at the next @act/@path."""
    out = []
    i = 0
    while i < len(s):
        if s[i] == "@" and (
                s.startswith("@act:", i) or s.startswith("@path:", i)):
            break
        if s[i] == " " and i + 1 < len(s) and s[i + 1] == "@":
            break
        out.append(s[i])
        i += 1
    return "".join(out).strip().strip("`").strip('"').strip("'")


def parse_l2_tags(text):
    """Pull the last @act and @path from L2 output. No regex."""
    act, path = "", ""
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("@act:") or lower.startswith("act:"):
            cut = line.split(":", 1)[1]
            val = _take_tag_value(cut)
            if val and not act:
                act = hyphen(val)
        elif lower.startswith("@path:") or lower.startswith("path:"):
            cut = line.split(":", 1)[1]
            val = _take_tag_value(cut)
            if val and not path:
                path = hyphen(val)
        else:
            i = 0
            while i < len(line):
                if line.startswith("@act:", i):
                    val = _take_tag_value(line[i + 5:])
                    if val and not act:
                        act = hyphen(val)
                    i += 5
                    continue
                if line.startswith("@path:", i):
                    val = _take_tag_value(line[i + 6:])
                    if val and not path:
                        path = hyphen(val)
                    i += 6
                    continue
                i += 1
    return act, path


def _direction_rest(path):
    for d in _DIRECTIONS:
        if path.startswith(d):
            return d, path[len(d):]
    return "", path


def _tag_tokens(text):
    """Hyphen and comma pieces. No regex."""
    out = []
    for raw in (text or "").replace(",", "-").split("-"):
        if raw:
            out.append(raw)
    return out


def marker_leak(act, path):
    """Leipzig labels quoted as tag content. Closed class. May fail the floor."""
    leaked = []
    seen = set()
    for w in _tag_tokens(act) + _tag_tokens(path):
        up = w.upper()
        if up in _LEIPZIG_MARKERS and w not in seen:
            seen.add(w)
            leaked.append(w)
    return leaked


def _is_nominal_noun(stem):
    low = (stem or "").lower()
    for end in _NOM_ENDS:
        if low.endswith(end) and len(low) > len(end):
            return True
    return False


def narrow_nominalisation(act):
    """True when the act is <verb> + <one noun in -tion/-ment/…>."""
    stems = [w for w in _tag_tokens(act) if w and w.lower() not in _THIN_STEMS]
    if len(stems) != 2:
        return False
    return (not _is_nominal_noun(stems[0])) and _is_nominal_noun(stems[1])


def exemplar_copied(japanese):
    """Exact match against L1 few-shot lines. A fact about two strings."""
    s = (japanese or "").strip()
    if not s:
        return False
    for ex in L1_EXEMPLARS:
        if s == ex:
            return True
    return False


def gloss_final_verb(interlinear):
    stems = content_stems(interlinear)
    return stems[-1] if stems else ""


def act_leading_verb(act):
    stems = [w for w in _tag_tokens(act) if w and w.lower() not in _THIN_STEMS]
    return stems[0].lower() if stems else ""


def convergence(act, interlinear):
    """Two independent routes. Agreement is evidence. Disagreement is a question.
    Never a score. Never a veto."""
    lead = act_leading_verb(act)
    final = gloss_final_verb(interlinear)
    if not lead or not final:
        return {"status": "not-looked-at", "lead": lead, "final": final}
    agree = lead == final or lead.startswith(final) or final.startswith(lead)
    return {
        "status": "agree" if agree else "disagree",
        "lead": lead,
        "final": final,
    }


def shape_witness(act, path):
    """Mechanical floor only. Never rewrites. pass / held / rephrase."""
    fails, held, passed = [], [], []
    if not act:
        fails.append("no-act")
    elif " " in act:
        fails.append("space-in-act")
    elif _direction_rest(act)[0] or act in _NAMED_EMPTY:
        fails.append("act-is-path")
    else:
        passed.append("has-act")

    leaked = marker_leak(act, path)
    if leaked:
        fails.append("marker-leak:" + ",".join(leaked))

    if act and narrow_nominalisation(act):
        fails.append("narrow-nominalisation")

    if not path:
        fails.append("no-path")
    elif path in _NAMED_EMPTY:
        held.append(path)
    elif " " in path:
        fails.append("space-in-path")
    else:
        prefix, rest = _direction_rest(path)
        if not prefix:
            fails.append("no-direction")
        else:
            passed.append("directional")
            stems = [w for w in rest.split("-") if w and w not in _THIN_STEMS]
            if not stems:
                fails.append("vacuous-path")
            elif len(stems) == 1:
                passed.append("stems:1")
            else:
                passed.append("stems:2+")

    if held and not fails:
        verdict = "held"
    elif not fails:
        verdict = "pass"
    else:
        verdict = "rephrase"
    ok = verdict in ("pass", "held") and bool(act)
    return {
        "verdict": verdict,
        "ok": ok,
        "fails": fails,
        "held": held,
        "passed": passed,
    }


def gloss_stems(interlinear):
    stems = set()
    for piece in (interlinear or "").split():
        head = piece.split("-")[0].replace(".", "-")
        for part in head.split("-"):
            low = part.lower()
            if low and not part.isupper() and low not in _THIN_STEMS:
                stems.add(low)
    return stems


def off_gloss(act, path, interlinear):
    """Stems L2 invented that the gloss never showed. Direction words allowed."""
    allowed = gloss_stems(interlinear)
    extra = []
    for w in (act or "").split("-"):
        if w and w not in _THIN_STEMS and w not in allowed:
            extra.append(w)
    _prefix, rest = _direction_rest(path or "")
    if path in _NAMED_EMPTY:
        rest = ""
    for w in rest.split("-"):
        if w and w not in _THIN_STEMS and w not in allowed:
            extra.append(w)
    return extra


def propose_from_gloss(interlinear):
    """Deterministic: first verb-ish token → act; nouns → toward-… or empty.

    Kept for tests and as a labelled clerk-guess in the walk body.
    Not the production last hop.
    """
    skip = {
        "SEQ", "AUX", "CASE", "TOP", "ADV.P", "SFP", "NMLZ", "AUX.V",
        "ACC", "NOM", "DAT", "ALL", "LOC", "ABL", "TERM", "COM", "GEN",
        "PROG", "RES", "PREP", "COMPL", "TRY", "BEN", "the", "a", "an",
    }
    tokens = []
    for raw in (interlinear or "").split():
        piece = raw.strip()
        if not piece:
            continue
        stem = piece.split("-")[0]
        stem = stem.replace(".", "-")
        tokens.append((piece, stem))
    verbs, nouns = [], []
    for piece, stem in tokens:
        up = stem.upper()
        if up in skip or stem.endswith("?"):
            continue
        if piece.endswith("-go") or "-SEQ-" in piece or "-SEQ" in piece:
            verbs.append(stem.lower())
            continue
        if stem[0:1].islower() or (stem and stem[0].isalpha()):
            nouns.append(stem.lower())
    act = ""
    if verbs:
        act = "-".join(verbs[:3])
    path = "not-yet-discerned"
    content = [n for n in nouns if n not in verbs]
    if len(content) >= 2:
        path = "toward-" + "-".join(content[:4])
    elif len(content) == 1 and verbs:
        path = "toward-the-" + content[0]
    return act, path


def propose_from_sample_chain(interlinear):
    """Tighter read of a Leipzig line like 'sky cross.over-SEQ-go'."""
    if not interlinear:
        return "", "not-yet-discerned"
    parts = interlinear.split()
    verbs, nouns = [], []
    for p in parts:
        if "-SEQ" in p or p.endswith("-go") or p.endswith("-come"):
            head = p.split("-")[0].replace(".", "-")
            if head:
                verbs.append(head.lower())
            if p.endswith("-go"):
                verbs.append("go")
            if p.endswith("-come"):
                verbs.append("come")
        elif p[0:1].isalpha() and not p.isupper():
            nouns.append(p.replace(".", "-").lower())
    act = "-".join([v for v in verbs if v]) or ""
    if len(nouns) >= 2:
        path = "toward-" + "-".join(nouns[:4])
    elif len(nouns) == 1:
        path = "toward-the-" + nouns[0]
    else:
        path = "not-yet-discerned"
    return act, path


def run_stack(asked, answered, written_act="", written_path=""):
    """Returns a dict /walk can show. Never raises out. Never a filing order.

    L1 + gloss always. L2 only when no written tag — displayed, not filed.
    A written tag is witnessed against the gloss (convergence), not replaced.
    """
    report = {
        "ok": False,
        "japanese": "",
        "gloss": "",
        "act": "",
        "path": "not-yet-discerned",
        "error": "",
        "raw_gloss": "",
        "l2": "",
        "verdict": "",
        "witness": {},
        "clerk_guess_act": "",
        "clerk_guess_path": "",
        "off_gloss": [],
        "source": "proposed",
        "convergence": {},
        "exemplar_copy": False,
        "input_cut": "",
    }
    try:
        raw_ja, cut_note = dango_japanese(asked, answered)
        report["input_cut"] = cut_note
        ja = japanese_span(first_sentence(raw_ja))
        report["japanese"] = ja
        if not ja or not looks_japanese(ja):
            report["error"] = "Dango produced no Japanese"
            return report
        if exemplar_copied(ja):
            report["exemplar_copy"] = True
            report["error"] = "L1 copied a prompt exemplar (exact match)"
            report["verdict"] = "rephrase"
            return report
        inter, raw = run_gloss(ja)
        report["gloss"] = inter
        report["raw_gloss"] = raw
        guess_act, guess_path = propose_from_sample_chain(inter)
        if not guess_act:
            guess_act, guess_path = propose_from_gloss(inter)
        report["clerk_guess_act"] = guess_act
        report["clerk_guess_path"] = guess_path

        written = bool(written_act)
        if written:
            report["source"] = "written"
            act = written_act
            path = written_path or "not-yet-discerned"
            report["convergence"] = convergence(act, inter)
        else:
            if not content_stems(inter):
                report["error"] = "gloss had no English stems for L2"
                report["verdict"] = "held"
                report["path"] = "not-yet-discerned"
                report["witness"] = shape_witness("", "not-yet-discerned")
                return report
            l2 = granite_l2_tags(ja, inter or ja)
            report["l2"] = l2
            report["l2_engine"] = "granite"
            act, path = parse_l2_tags(l2)
            if not path:
                path = "not-yet-discerned"

        invented = off_gloss(act, path, inter)
        report["off_gloss"] = invented
        wit = shape_witness(act, path)
        report["witness"] = wit
        report["verdict"] = wit["verdict"]
        # Shown, never a filing order. run.py must not copy these onto the turn.
        report["act"] = act
        report["path"] = path
        report["ok"] = wit["ok"]
        if not wit["ok"]:
            report["error"] = (
                ("written" if written else "L2")
                + " tags rephrase: " + ",".join(wit["fails"] or ["empty"]))
    except Exception as e:
        report["error"] = str(e)
    return report


def stack_as_walk_text(report):
    lines = ["PATH STACK (summoned. Proposed tags are not filed.)"]
    if report.get("source") == "written":
        lines.append("source: written tag on the turn — witnessed, not replaced")
    else:
        lines.append("source: proposed by the stack — not filed on the turn")
    if report.get("error"):
        lines.append("error: " + report["error"])
    if report.get("input_cut"):
        lines.append(report["input_cut"])
    if report.get("exemplar_copy"):
        lines.append("exemplar-copy: exact match against an L1 few-shot line")
    if report.get("japanese"):
        lines.append("japanese: " + report["japanese"])
    if report.get("gloss"):
        lines.append("gloss: " + report["gloss"])
    if report.get("l2"):
        compact = " | ".join(
            ln.strip() for ln in report["l2"].splitlines() if ln.strip())
        engine = report.get("l2_engine") or "l2"
        lines.append("l2 " + engine + " (not filed): " + compact)
    if report.get("verdict"):
        lines.append("verdict: " + report["verdict"])
    wit = report.get("witness") or {}
    if wit.get("fails"):
        lines.append("fails: " + ",".join(wit["fails"]))
    if wit.get("held"):
        lines.append("held: " + ",".join(wit["held"]))
    if report.get("off_gloss"):
        lines.append("stems-not-in-gloss (witness, not a veto): "
                     + ",".join(report["off_gloss"]))
    conv = report.get("convergence") or {}
    if conv.get("status"):
        lines.append(
            "convergence: " + conv["status"]
            + " (act-lead=" + (conv.get("lead") or "-")
            + " gloss-final=" + (conv.get("final") or "-") + ")")
    if report.get("act"):
        lines.append("@act:" + report["act"])
    lines.append("@path:" + (report.get("path") or "not-yet-discerned"))
    if report.get("clerk_guess_act") or report.get("clerk_guess_path"):
        lines.append(
            "clerk-guess (not filed): @act:"
            + (report.get("clerk_guess_act") or "(none)")
            + " @path:" + (report.get("clerk_guess_path") or "not-yet-discerned"))
    return "\n".join(lines)
