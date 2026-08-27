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
    kept, n_kept, n_all, dropped, cut = place_fit.fit_in_order(
        "aaaa\n\nbbbb\n\ncccc", 10000)
    if n_kept != 3 or n_all != 3 or dropped != 0 or cut or "cccc" not in kept:
        fails.append("wide budget must keep all: " + repr(
            (kept, n_kept, n_all, dropped, cut)))
    tiny = place_fit.estimate_tokens("aaaa")
    kept, n_kept, n_all, dropped, cut = place_fit.fit_in_order(
        "aaaa\n\nbbbb\n\ncccc", tiny)
    if n_kept != 1 or n_all != 3 or dropped != 2 or kept != "aaaa" or cut:
        fails.append("tight budget must keep first paragraph only: " + repr(
            (kept, n_kept, n_all, dropped, cut)))
    note = place_fit.drop_note(n_kept, n_all, dropped, cut)
    if "paragraphs 2-3" not in note or "not a relevance pick" not in note:
        fails.append("drop_note must name the cut in document order: "
                     + repr(note))
    kept, n_kept, n_all, dropped, cut = place_fit.fit_in_order(
        "huge paragraph", 1)
    if not kept or dropped != 1 or cut != "chars":
        fails.append("oversized first paragraph must keep a prefix: "
                     + repr((kept, n_kept, n_all, dropped, cut)))
    if "huge paragraph" in kept and kept == "huge paragraph":
        fails.append("prefix must be shorter than the whole first paragraph")
    note = place_fit.drop_note(n_kept, n_all, dropped, cut)
    if "remainder of paragraph 1" not in note or "not a relevance pick" not in note:
        fails.append("drop_note must name a prefix cut: " + repr(note))
    lined = "short line\n" + ("word " * 80)
    tiny_line = place_fit.estimate_tokens("short line")
    kept, n_kept, n_all, dropped, cut = place_fit.fit_in_order(
        lined, tiny_line)
    if "short line" not in kept or "word word" in kept or cut != "lines":
        fails.append("oversized paragraph must keep first line: "
                     + repr((kept, n_kept, n_all, dropped, cut)))
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
