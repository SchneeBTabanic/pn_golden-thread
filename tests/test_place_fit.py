#!/usr/bin/env python3
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import place_fit  # noqa: E402


def run():
    fails = []
    paras = place_fit.split_paragraphs("one\n\ntwo\n\nthree")
    if paras != ["one", "two", "three"]:
        fails.append("split_paragraphs drifted: " + repr(paras))
    kept, n_kept, n_all, dropped = place_fit.fit_in_order(
        "aaaa\n\nbbbb\n\ncccc", 10000)
    if n_kept != 3 or n_all != 3 or dropped != 0 or "cccc" not in kept:
        fails.append("wide budget must keep all: " + repr(
            (kept, n_kept, n_all, dropped)))
    tiny = place_fit.estimate_tokens("aaaa")
    kept, n_kept, n_all, dropped = place_fit.fit_in_order(
        "aaaa\n\nbbbb\n\ncccc", tiny)
    if n_kept != 1 or n_all != 3 or dropped != 2 or kept != "aaaa":
        fails.append("tight budget must keep first paragraph only: " + repr(
            (kept, n_kept, n_all, dropped)))
    note = place_fit.drop_note(n_kept, n_all, dropped)
    if "paragraphs 2-3" not in note or "not a relevance pick" not in note:
        fails.append("drop_note must name the cut in document order: "
                     + repr(note))
    kept, n_kept, n_all, dropped = place_fit.fit_in_order("huge paragraph", 1)
    if kept != "" or dropped != 1:
        fails.append("first paragraph larger than budget must keep nothing: "
                     + repr((kept, n_kept, n_all, dropped)))
    src = open(os.path.join(HERE, "place_fit.py"), encoding="utf-8").read()
    for banned in ("score_passages(", "TextRank(", "cosine("):
        if banned in src:
            fails.append("place_fit grew a ranker: " + banned)
    src_run = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if "place_fit.fit_in_order" not in src_run:
        fails.append("run.py must fit file:/url: in document order")
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — place_fit is document order, not a selector")
    return 0


if __name__ == "__main__":
    sys.exit(run())
