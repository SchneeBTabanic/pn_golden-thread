"""
place_fit.py — fill the face window in document order. No ranking.

file: / url: / html: may be smaller than GT_FILE_MAX_BYTES and still
too big for n_ctx. Walk paragraphs in the order they already have.
Keep a prefix that fits. Name what was dropped. Do not score, BM25,
embed, or pick "relevant" passages.
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


def estimate_tokens(text):
    """Same 3 chars/token rule as sheet_fits_ctx. Not a ranking."""
    return (len(text or "") + 2) // 3


def fit_in_order(text, budget, count_tokens=None):
    """Keep a document-order prefix that fits `budget` tokens.

    Returns (kept_text, n_kept, n_all, dropped_from).
    dropped_from is 1-based paragraph index of the first drop, or 0
    if nothing was dropped. If paragraph 1 does not fit, kept is empty.
    """
    count = count_tokens or estimate_tokens
    try:
        budget = int(budget)
    except (TypeError, ValueError):
        budget = 0
    paras = split_paragraphs(text)
    n_all = len(paras)
    if n_all == 0:
        return "", 0, 0, 0
    if budget <= 0:
        return "", 0, n_all, 1
    kept = []
    used = 0
    for p in paras:
        need = count(p)
        extra = 2 if kept else 0
        if used + extra + need > budget:
            break
        kept.append(p)
        used += extra + need
    n_kept = len(kept)
    if n_kept == 0:
        return "", 0, n_all, 1
    dropped_from = 0 if n_kept == n_all else n_kept + 1
    return "\n\n".join(kept), n_kept, n_all, dropped_from


def drop_note(n_kept, n_all, dropped_from):
    """English for the clerk banner. Empty if the whole document fitted."""
    if n_all <= 0 or dropped_from <= 0 or n_kept >= n_all:
        return ""
    return (
        "DROPPED: paragraphs " + str(dropped_from) + "-" + str(n_all)
        + " (past the face window; document order, not a relevance pick). "
        + str(n_kept) + " of " + str(n_all) + " paragraphs placed."
    )
