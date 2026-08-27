"""
place_fit.py — fill the face window in document order. No ranking.

file: / url: / html: may be smaller than GT_FILE_MAX_BYTES and still
too big for n_ctx. Walk units in the order they already have.
Keep a prefix that fits. Name what was dropped. Do not score, BM25,
embed, or pick "relevant" passages.

If a blank-line paragraph is itself larger than the remaining window,
split that paragraph in order: lines, then sentences, then a character
prefix. Still not a relevance pick.
"""


def split_paragraphs(text):
    """Blank-line paragraphs. No regex. Original order."""
    parts = []
    buf = []
    for line in (text or "").splitlines():
        if line.strip() == "":
            if buf:
                parts.append("\n".join(buf))
                buf = []
        else:
            buf.append(line)
    if buf:
        parts.append("\n".join(buf))
    return parts


def split_lines(text):
    """Non-empty lines, original order. No regex."""
    out = []
    for line in (text or "").splitlines():
        if line.strip():
            out.append(line)
    return out


def split_sentences(text):
    """Document-order sentences. No regex. Abbreviations may split; named poverty."""
    seps = set(".?!。！？")
    parts = []
    buf = []
    s = text or ""
    n = len(s)
    i = 0
    while i < n:
        ch = s[i]
        buf.append(ch)
        if ch in seps:
            nxt = s[i + 1] if i + 1 < n else ""
            cjk = ch in "。！？"
            if cjk or nxt == "" or nxt in " \t\n\r":
                piece = "".join(buf).strip()
                if piece:
                    parts.append(piece)
                buf = []
        i += 1
    rest = "".join(buf).strip()
    if rest:
        parts.append(rest)
    return parts


def estimate_tokens(text):
    """Same 3 chars/token rule as sheet_fits_ctx. Not a ranking."""
    return (len(text or "") + 2) // 3


def prefix_to_budget(text, budget, count):
    """Longest document-order prefix of `text` that fits `budget`. No regex."""
    if budget <= 0 or not text:
        return ""
    if count(text) <= budget:
        return text
    lo = 0
    hi = len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if count(text[:mid]) <= budget:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo]


def _join_fit(parts, joiner, budget, count):
    """Keep a prefix of parts joined by joiner. Returns (kept, n_kept)."""
    kept = []
    for p in parts:
        cand = joiner.join(kept + [p])
        if count(cand) > budget:
            break
        kept.append(p)
    return joiner.join(kept), len(kept)


def _prefix_of_unit(text, budget, count):
    """Smaller units of one paragraph, still in order. Returns (kept, how)."""
    lines = split_lines(text)
    if len(lines) > 1:
        kept, n = _join_fit(lines, "\n", budget, count)
        if kept:
            if n < len(lines):
                return kept, "lines"
            return kept, "whole"
        # first line itself too big
        return _prefix_of_unit(lines[0], budget, count)
    sents = split_sentences(text)
    if len(sents) > 1:
        kept, n = _join_fit(sents, " ", budget, count)
        if kept:
            if n < len(sents):
                return kept, "sentences"
            return kept, "whole"
        return _prefix_of_unit(sents[0], budget, count)
    cut = prefix_to_budget(text, budget, count)
    if cut:
        return cut, "chars"
    return "", "none"


def fit_in_order(text, budget, count_tokens=None):
    """Keep a document-order prefix that fits `budget` tokens.

    Returns (kept_text, n_kept, n_all, dropped_from, cut).
    dropped_from is 1-based paragraph index of the first incomplete or
    dropped paragraph, or 0 if nothing was dropped.
    cut is "" when every kept paragraph is whole; otherwise how the
    first incomplete paragraph was reduced (lines/sentences/chars).
    """
    count = count_tokens or estimate_tokens
    try:
        budget = int(budget)
    except (TypeError, ValueError):
        budget = 0
    paras = split_paragraphs(text)
    n_all = len(paras)
    if n_all == 0:
        return "", 0, 0, 0, ""
    if budget <= 0:
        return "", 0, n_all, 1, "none"
    kept = []
    cut = ""
    dropped_from = 0
    for i, p in enumerate(paras):
        cand = "\n\n".join(kept + [p]) if kept else p
        if count(cand) <= budget:
            kept.append(p)
            continue
        remain = budget - (count("\n\n".join(kept)) if kept else 0)
        if kept:
            remain = remain - count("\n\n")
        if remain < 0:
            remain = 0
        piece, how = _prefix_of_unit(p, remain, count)
        if piece:
            maybe = "\n\n".join(kept + [piece]) if kept else piece
            if count(maybe) <= budget:
                kept.append(piece)
                cut = how
                dropped_from = i + 1
                break
        dropped_from = i + 1
        break
    n_kept = len(kept)
    if n_kept == 0:
        return "", 0, n_all, 1, cut or "none"
    if dropped_from == 0 and n_kept < n_all:
        dropped_from = n_kept + 1
    if dropped_from == 0:
        cut = ""
    body = "\n\n".join(kept)
    # whole paragraphs only: n_kept counts pieces including a prefix
    n_whole = n_kept - (1 if cut else 0)
    return body, n_whole, n_all, dropped_from, cut


def drop_note(n_kept, n_all, dropped_from, cut=""):
    """English for the clerk banner. Empty if the whole document fitted."""
    if n_all <= 0 or dropped_from <= 0:
        return ""
    if not cut and n_kept >= n_all:
        return ""
    if cut and cut not in ("", "none"):
        rest = ""
        if dropped_from < n_all:
            rest = (
                "; paragraphs " + str(dropped_from + 1) + "-" + str(n_all)
                + " not placed"
            )
        return (
            "DROPPED: remainder of paragraph " + str(dropped_from)
            + " after a document-order " + cut + " prefix" + rest
            + " (past the face window; not a relevance pick). "
            + str(n_kept) + " of " + str(n_all)
            + " paragraphs placed whole."
        )
    return (
        "DROPPED: paragraphs " + str(dropped_from) + "-" + str(n_all)
        + " (past the face window; document order, not a relevance pick). "
        + str(n_kept) + " of " + str(n_all) + " paragraphs placed."
    )
