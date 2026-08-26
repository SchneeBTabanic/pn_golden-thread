"""
gloss.py — the deterministic back-translator (Leipzig-style interlinear).
=========================================================================

SETUP PROOF, not production. Built 2026-07-26 to show the deterministic half of the
tag pipeline works before any model is put in front of it — the recorded prep order
(small-over-power): *install the light glosser FIRST and prove it on a sample,
BEFORE the heavy forward-LLM.*

WHAT THIS IS FOR. The pipeline needs a Japanese→English step that **cannot
domesticate**. An LLM asked to "translate" produces fluent English and erases the
structure that was the whole point. A gloss cannot: it walks the morphemes in
Japanese order and maps each by rule, so the verb-framing survives by construction.

    空越えていく  →  sky  cross-SEQ-go

WHAT IT DOES AND DOES NOT DO
  * DOES: segment, lemmatise, and map grammatical function to Leipzig-style labels
    from SudachiPy's part-of-speech features. Deterministic — same input, same
    output, no model, no network.
  * DOES: gloss lemmas from JMdict (EDRDG, CC BY-SA 4.0), extracted once into a
    plain-text table we own — `jmdict-lemmas.tsv`, 593,641 rows. A lemma with no
    entry is printed in Japanese and MARKED, never guessed at and never silently
    dropped (§3.8 — a missing gloss must not look like a translated one).
  * DOES NOT: choose between senses by its own judgement. Where a form is
    ambiguous, JMdict's OWN commonness markers (ichi1/news1/spec1…) decided it at
    extraction time.

The label set below is a CLOSED grammatical class — Japanese particle and auxiliary
functions, finite and stable — which is the only kind of word set this project
allows (see `feedback-structure-not-filters`). It is not a vocabulary and must
never grow into one.

Run:  .venv/bin/python3 gloss.py '空越えていく'
"""

import os
import sys

from sudachipy import Dictionary, SplitMode

LEXICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jmdict-lemmas.tsv")


def load_lexicon(path=LEXICON):
    """The JMdict lemma glosses as a plain-text table we own — `lemma<TAB>reading
    <TAB>class<TAB>rank<TAB>gloss`. Keyed by (lemma, reading, class) because the
    reading is what disambiguates: 空/ソラ is sky, 空/カラ is empty, and SudachiPy
    hands us the reading. Where a form is still ambiguous, JMdict's OWN commonness
    rank decided it at build time — no sense-choice here is mine.

    Missing file is NAMED, not silently treated as an empty lexicon (§3.8): an
    absent dictionary and a dictionary with no match must not look alike.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"lexicon not built: {path} — run the JMdict extraction first")
    lex, by_lemma = {}, {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 5:
                lemma, reading, cls, rank, gloss = parts
                lex[(lemma, reading, cls)] = gloss
                r = int(rank)
                if lemma not in by_lemma or r < by_lemma[lemma][0]:
                    by_lemma[lemma] = (r, gloss)
    lex["__by_lemma__"] = {k: v[1] for k, v in by_lemma.items()}
    return lex


def look_up(lex, lemma, reading, label):
    """(lemma, reading, class) first; then the same lemma under any class, since
    SudachiPy's class and JMdict's part-of-speech do not always agree. Returns
    None when nothing matches — the caller marks it, never invents it."""
    cls = {"N": "N", "V": "V", "ADJ": "ADJ", "ADJ.N": "ADJ", "AUX.V": "V"}.get(label)
    for key in ((lemma, reading, cls), (lemma, reading, "-"),
                (lemma, reading, "N"), (lemma, reading, "V")):
        if key[2] and key in lex:
            return lex[key]
    # SudachiPy's reading_form() is the SURFACE reading of an inflected token
    # (越え -> コエ), not the dictionary form's reading (コエル), so a conjugated
    # verb misses the reading-keyed index. Fall back to the lemma alone, taking
    # JMdict's highest-ranked sense — still the data's choice, not ours.
    return lex.get("__by_lemma__", {}).get(lemma)

# Leipzig-style function labels, keyed by SudachiPy's own POS field. A CLOSED set:
# these are grammatical functions, not words, and the list cannot grow with content.
_FUNCTION = {
    "接続助詞": "SEQ",     # conjunctive particle — links the verb chain
    "格助詞": "CASE",      # case particle (を ACC, が NOM, に DAT …)
    "係助詞": "TOP",       # topic/binding particle (は)
    "副助詞": "ADV.P",     # adverbial particle
    "終助詞": "SFP",       # sentence-final particle
    "準体助詞": "NMLZ",    # nominaliser
    "助動詞": "AUX",       # auxiliary verb
    "非自立可能": "AUX.V",  # non-independent verb — the directional/aspectual tail
}

# Case particles carry the relation that matters most for act-and-path, so they are
# named individually rather than flattened to CASE.
_CASE = {"を": "ACC", "が": "NOM", "に": "DAT", "へ": "ALL", "で": "LOC",
         "から": "ABL", "まで": "TERM", "と": "COM", "の": "GEN"}

_CONTENT = {"名詞": "N", "動詞": "V", "形容詞": "ADJ", "形状詞": "ADJ.N", "副詞": "ADV"}

# The Japanese auxiliary verbs (補助動詞) in their GRAMMATICAL use. A genuinely
# closed class — the language has a handful and cannot grow more — which is why
# glossing them by function is allowed where a vocabulary list would not be.
# They must NOT be looked up in JMdict: its highest-ranked いる is 入る "enter",
# so a dictionary hit here is confidently wrong. Grammar, not vocabulary.
_AUX_VERB = {"いく": "go", "行く": "go", "くる": "come", "来る": "come",
             "いる": "PROG", "居る": "PROG", "ある": "RES", "有る": "RES",
             "おく": "PREP", "置く": "PREP", "しまう": "COMPL",
             "みる": "TRY", "見る": "TRY", "あげる": "BEN", "くれる": "BEN.in",
             "もらう": "BEN.rcv"}


def gloss(text: str, tokenizer=None):
    """Return a list of (surface, lemma, label) in JAPANESE ORDER.

    `label` is a grammatical function for function words, a category for content
    words. Nothing is reordered into English syntax — that reordering is exactly
    the domestication this step exists to prevent.
    """
    tok = tokenizer or Dictionary().create()
    out = []
    for m in tok.tokenize(text, SplitMode.C):
        pos = m.part_of_speech()
        surface, lemma = m.surface(), m.dictionary_form()
        label = None
        for field in pos:
            # A case particle is named individually ONLY when SudachiPy says it is
            # acting as one. で in 読んで is the voiced te-form (接続助詞), not the
            # locative 格助詞 — preferring the surface form flattened the verb chain
            # into "read LOC", which is the domestication this step exists to stop.
            if field == "格助詞" and surface in _CASE:
                label = _CASE[surface]
                break
            if field in _FUNCTION:
                label = _FUNCTION[field]
                break
        if label is None:
            label = _CONTENT.get(pos[0], pos[0])
        out.append((surface, lemma, m.reading_form(), label))
    return out


def render(rows, lexicon=None) -> str:
    """Interlinear line. Content lemmas are looked up in `lexicon` if one is given;
    otherwise they are shown in Japanese and marked with '?' — a missing gloss is
    NAMED, never invented (§3.8). JMdict is not installed, so today every content
    word is marked."""
    lexicon = lexicon or {}
    parts = []
    for surface, lemma, reading, label in rows:
        # A directional auxiliary (いく/くる — SudachiPy's 非自立可能) keeps its
        # LEXICAL content and is glossed by meaning, not by function: the hyphen
        # already shows the attachment, so labelling it AUX.V would throw away the
        # very thing being glossed. Caught by the recorded acceptance sample, which
        # wants `cross-SEQ-go`, not `cross-SEQ-AUX.V`.
        if label == "AUX.V":
            # Grammar, by the closed class above — never a dictionary lookup.
            parts.append(_AUX_VERB.get(lemma, "AUX.V"))
            continue
        if label in ("N", "V", "ADJ", "ADJ.N", "ADV"):
            en = look_up(lexicon, lemma, reading, label)
            # LEIPZIG RULE 4: one morpheme = one gloss TOKEN. Where English needs
            # several words for a single Japanese morpheme, they are joined with
            # periods, never spaces — "cross over" would read as two morphemes and
            # quietly turn the line back into English prose. This is the difference
            # between grammar seen through Japanese eyes that borrows English
            # markers, and English wearing a gloss.
            if en:
                en = en.replace(" ", ".")
            parts.append(en if en else (f"{lemma}?" if label != "AUX.V" else "AUX.V"))
        else:
            parts.append(label)
    # verb-tail labels attach to the preceding element with a hyphen, Leipzig-style
    line, prev_content = [], False
    for (surface, lemma, reading, label), piece in zip(rows, parts):
        if label in ("SEQ", "AUX", "AUX.V") and prev_content and line:
            line[-1] = line[-1] + "-" + piece
        else:
            line.append(piece)
        prev_content = label in ("N", "V", "ADJ", "ADJ.N", "ADV", "SEQ", "AUX", "AUX.V")
    return " ".join(line)


if __name__ == "__main__":
    texts = sys.argv[1:] or ["空越えていく"]
    tk = Dictionary().create()
    for t in texts:
        rows = gloss(t, tk)
        lex = load_lexicon()
        print(f"\n{t}")
        for surface, lemma, reading, label in rows:
            print(f"  {surface:8} {lemma:10} {reading:10} {label}")
        print(f"  → {render(rows, lex)}")
    print("\nA lemma with no JMdict entry is printed in Japanese and marked '?' — "
          "marked, never guessed.")
