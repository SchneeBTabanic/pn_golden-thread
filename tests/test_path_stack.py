#!/usr/bin/env python3
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import model  # noqa: E402
import path_stack  # noqa: E402


def run():
    fails = []
    lab = ("/home/schnee", "ProjectNamirha_git", "/mnt/data/Codeberg")
    if not os.environ.get("GT_DANGO"):
        for needle in lab:
            if needle in path_stack.DANGO_DIR:
                fails.append("default DANGO_DIR is a lab machine path: "
                             + path_stack.DANGO_DIR)
    if not os.environ.get("GT_GLOSS_PY"):
        for needle in lab:
            if needle in path_stack.GLOSS_PY:
                fails.append("default GLOSS_PY is a lab machine path: "
                             + path_stack.GLOSS_PY)

    wrapped = model.granite_chat("Hello", [("Hi", "Hello there.")])
    if "<|start_of_role|>user<|end_of_role|>Hello" not in wrapped:
        fails.append("chat wrap lost the user turn")
    if "<|start_of_role|>assistant<|end_of_role|>" not in wrapped:
        fails.append("chat wrap has no assistant opener")
    if wrapped.strip().endswith("Hello"):
        fails.append("chat wrap looks like raw completion")

    import run as runmod
    sheet = path_stack.tag_sheet_live_core()
    if "TAG SHEET ABSENT" in sheet or "TAG SHEET EMPTY" in sheet:
        fails.append("gForth tag sheet is missing at the default path")
    if "@act:" not in sheet or "not-yet-discerned" not in sheet:
        fails.append("tag sheet lost live-core meanings")
    if "\n## 3." in sheet:
        fails.append("live core included the whole sheet (too big for the 8B)")
    beneath = path_stack.tag_sheet_beneath()
    if "TAG SHEET ABSENT" in beneath or "TAG SHEET EMPTY" in beneath:
        fails.append("beneath sheet missing")
    if "\n## 3." not in beneath or "\n## 5." not in beneath:
        fails.append("beneath must be the whole sheet, not a live-core")
    if "No live-core" not in beneath:
        fails.append("beneath must say it is not a live-core")
    if "SHEET CUT" in beneath:
        fails.append("beneath must not designer-cut the sheet")
    if "Walk every key" in beneath:
        fails.append("beneath revived the register-as-menu walk")
    whole = path_stack.tag_sheet_text()
    ok4, need4, _c4 = path_stack.sheet_fits_ctx(4096, whole, "asked", "answered")
    if ok4:
        fails.append("4096 ctx must not pretend to hold the whole sheet")
    ok8, _n8, _c8 = path_stack.sheet_fits_ctx(8192, whole, "asked", "answered")
    if not ok8:
        fails.append("8192 ctx should hold the whole sheet on this budget: need "
                     + str(need4))
    if "Walk every key" in runmod.LOOK_SYSTEM:
        fails.append("LOOK_SYSTEM revived the register-as-menu walk")
    src_stack = open(os.path.join(HERE, "path_stack.py"), encoding="utf-8").read()
    run_chunk = src_stack.split("def run_stack(", 1)[1].split(
        "def stack_as_walk_text(", 1)[0]
    if "dango_l2_tags(" in run_chunk:
        fails.append("run_stack still asks Dango for English L2")
    if "granite_l2_tags(" not in run_chunk:
        fails.append("run_stack must call granite_l2_tags")

    src = open(os.path.join(HERE, "model.py"), encoding="utf-8").read()
    for fn in ("def shape(", "def comment(", "def look("):
        if fn not in src:
            fails.append(f"{fn} missing")
    # The three summons must go through _as_chat, not raw template completion.
    after_shape = src.split("def shape(", 1)[1].split("def comment(", 1)[0]
    after_comment = src.split("def comment(", 1)[1].split("def look(", 1)[0]
    after_look = src.split("def look(", 1)[1].split("def walker(", 1)[0]
    for name, chunk in (
            ("shape", after_shape), ("comment", after_comment),
            ("look", after_look)):
        if "_as_chat(" not in chunk:
            fails.append(f"{name}() is not chat-wrapped")
        if 'f"{system_prompt}\\n\\n{user_prompt}' in chunk:
            fails.append(f"{name}() still concatenates as a document")

    act, path = path_stack.propose_from_sample_chain("sky cross.over-SEQ-go")
    if "cross" not in act:
        fails.append(f"sample gloss lost the verb: {act!r}")
    if "sky" not in path:
        fails.append(f"sample gloss lost the noun: {path!r}")

    act, path = path_stack.parse_l2_tags(
        "@act:cross-over-go\n@path:toward-the-sky")
    if act != "cross-over-go" or path != "toward-the-sky":
        fails.append(f"two-line L2 parse: {act!r} {path!r}")
    act, path = path_stack.parse_l2_tags(
        "please write @act:ask-a-question @path:toward-the-greeting")
    if act != "ask-a-question" or "greeting" not in path:
        fails.append(f"inline L2 parse: {act!r} {path!r}")
    act, path = path_stack.parse_l2_tags("act: greet the person\npath: toward a hello")
    if " " in act or " " in path:
        fails.append(f"L2 spaces not hyphenated: {act!r} {path!r}")
    if "greet" not in act or "hello" not in path:
        fails.append(f"L2 hyphen lost stems: {act!r} {path!r}")

    w = path_stack.shape_witness("cross-over-go", "toward-the-open-sky")
    if w["verdict"] != "pass" or not w["ok"]:
        fails.append(f"two-stem path should pass: {w}")
    if "stems:2+" not in w["passed"]:
        fails.append(f"stem count should be a note, not concrete: {w}")
    w = path_stack.shape_witness("greet", "toward-the-sky")
    if w["verdict"] != "pass" or not w["ok"]:
        fails.append(f"one-stem path should pass: {w}")
    if "stems:1" not in w["passed"] or "thin-path" in w["held"]:
        fails.append(f"one stem must not hold the tag back: {w}")
    w = path_stack.shape_witness("greet", "not-yet-discerned")
    if w["verdict"] != "held" or not w["ok"]:
        fails.append(f"named empty should hold: {w}")
    w = path_stack.shape_witness("greet", "a-nice-chat")
    if w["verdict"] != "rephrase" or w["ok"]:
        fails.append(f"no direction should rephrase: {w}")
    w = path_stack.shape_witness("", "toward-the-sky")
    if w["ok"]:
        fails.append("empty act must not be filed")
    w = path_stack.shape_witness("toward-the-how", "toward-the-how")
    if w["ok"] or "act-is-path" not in w["fails"]:
        fails.append(f"act that is a path must rephrase: {w}")

    extra = path_stack.off_gloss(
        "open-put-in", "toward-window-wind",
        "window open-SEQ wind put.in")
    if extra:
        fails.append(f"gloss stems should be allowed: {extra}")
    extra = path_stack.off_gloss(
        "open-put-in", "toward-the-wind",
        "sky bird cross.over-SEQ-go")
    if "wind" not in extra:
        fails.append(f"invented path stem must be off-gloss: {extra}")
    # A faithful paraphrase must not be vetoed. The bench-sheet example:
    invented = path_stack.off_gloss(
        "protect-against-bit-rot",
        "toward-integrity-over-convenience",
        "NAS-TOP checksum-ACC snapshot-ACC keep-PROG")
    if not invented:
        fails.append("bench paraphrase should show stems-not-in-gloss")
    wit = path_stack.shape_witness(
        "protect-against-bit-rot",
        "toward-integrity-over-convenience")
    if not wit["ok"]:
        fails.append("shape floor must not reject the bench paraphrase")

    leak = path_stack.marker_leak("ACC,ACC,ACC,ACC", "toward-rule-go")
    if "ACC" not in leak:
        fails.append(f"Leipzig ACC must leak: {leak}")
    leak = path_stack.marker_leak("rule-AUX-go", "toward-rule-go")
    if "AUX" not in leak:
        fails.append(f"Leipzig AUX must leak: {leak}")
    leak = path_stack.marker_leak("keep-checksum", "toward-snapshot")
    if leak:
        fails.append(f"content stems are not markers: {leak}")
    wit = path_stack.shape_witness("rule-AUX-go", "toward-rule-go")
    if wit["ok"] or not any(f.startswith("marker-leak:") for f in wit["fails"]):
        fails.append(f"marker leak must fail the floor: {wit}")

    if not path_stack.narrow_nominalisation("do-reconfirmation"):
        fails.append("verb + one -tion noun must be narrow nominalisation")
    if path_stack.narrow_nominalisation(
            "tell-association-apart-from-provenance"):
        fails.append("a doing with a named object must not be the narrow form")
    if path_stack.narrow_nominalisation("keep-checksum"):
        fails.append("ordinary two-stem act is not nominalisation")
    wit = path_stack.shape_witness("do-reconfirmation", "toward-the-question")
    if wit["ok"] or "narrow-nominalisation" not in wit["fails"]:
        fails.append(f"narrow nominalisation must fail the floor: {wit}")

    if not path_stack.exemplar_copied("空を鳥が渡っていく"):
        fails.append("L1 exemplar must count as a copy")
    if path_stack.exemplar_copied("索引を本文と取り違えるのをやめる"):
        fails.append("a different Japanese sentence is not an exemplar copy")

    class _CharTok:
        def encode(self, s, add_special_tokens=False):
            del add_special_tokens
            return list(s or "")

        def decode(self, ids, skip_special_tokens=True):
            del skip_special_tokens
            return "".join(ids)

    tok = _CharTok()
    kept, n, cut = path_stack.budget_text("abcdefghij", 4, tok)
    if kept != "abcd" or n != 10 or cut != 6:
        fails.append("budget_text must clip by tokens not characters of a slice: "
                     + repr((kept, n, cut)))
    kept, n, cut = path_stack.budget_text("abcd", 10, tok)
    if kept != "abcd" or n != 4 or cut != 0:
        fails.append("short text must stay whole: " + repr((kept, n, cut)))
    prompt, note = path_stack.l1_instruction_prompt(
        "What is 2+2?", "2 + 2 equals 4.", tok)
    if "空を鳥" in prompt or "窓を開けて" in prompt:
        fails.append("L1 prompt still carries topic exemplars")
    if "会話の動きを短い日本語の一文で書く" not in prompt:
        fails.append("L1 Japanese instruction missing")
    if "nothing cut" not in note:
        fails.append("zero cut must be named: " + repr(note))
    long_ans = "x" * 300
    _p, note2 = path_stack.l1_instruction_prompt("q", long_ans, tok)
    del _p
    if "cut " not in note2 or "nothing cut" in note2:
        fails.append("a cut must be named in-band: " + repr(note2))
    src = open(os.path.join(HERE, "path_stack.py"), encoding="utf-8").read()
    fn = src.split("def dango_japanese(", 1)[1].split("def content_stems(", 1)[0]
    if "first_sentence(asked)[:200]" in fn or "[:200]" in fn:
        fails.append("dango_japanese still slices ASKED/ANSWERED by characters")
    if "空を見て" in fn or "窓を開けて" in fn:
        fails.append("dango_japanese still contains topic exemplars")

    conv = path_stack.convergence(
        "stop-reading-hooks-as-the-corpus",
        "index ACC text COM mistake.one.thing.for.another NMLZ ACC stop")
    if conv["status"] != "agree":
        fails.append(f"same doing on two routes should agree: {conv}")
    conv = path_stack.convergence(
        "notice-the-law",
        "registry ACC implement-PROG")
    if conv["status"] != "disagree":
        fails.append(f"different verbs should disagree: {conv}")
    conv = path_stack.convergence("", "sky bird cross.over-SEQ-go")
    if conv["status"] != "not-looked-at":
        fails.append(f"empty act is not-looked-at: {conv}")

    act, path = path_stack.parse_l2_tags(
        "@act:return-an-answer\n@path:toward-the-question\n"
        "@act:toward-the-go\n@path:toward-the-wind")
    if act != "return-an-answer" or path != "toward-the-question":
        fails.append(f"first tag pair should win: {act!r} {path!r}")

    if path_stack.japanese_span("Hello! How can I为に尋ねる") != "为に尋ねる":
        fails.append("japanese_span should drop the Latin echo")

    stems = path_stack.content_stems(
        "代名詞 DAT go-AUX SFP COM do.up question DAT face-SEQ 補助記号 answer ACC return")
    for need in ("go", "question", "face", "answer", "return"):
        if need not in stems:
            fails.append(f"content stem missing {need}: {stems}")
    if "dat" in stems or "seq" in stems:
        fails.append(f"POS label leaked into stems: {stems}")
    sky = path_stack.content_stems("sky bird cross.over-SEQ-go")
    for need in ("sky", "bird", "cross", "over", "go"):
        if need not in sky:
            fails.append(f"sky gloss lost {need}: {sky}")

    if not path_stack.looks_japanese("空を鳥が渡っていく"):
        fails.append("kanji+kana should look Japanese")
    if path_stack.looks_japanese("Hello! How can I assist you today?"):
        fails.append("English Hello should not look Japanese")
    if path_stack.first_sentence("挨拶する\n人: Hello") != "挨拶する":
        fails.append("first_sentence should stop at newline")

    if not path_stack.dango_ready():
        print("NOTE — Dango weights not on disk; live stack not tested")
    if not path_stack.gloss_ready():
        fails.append("gloss.py / venv missing — midwife stack is not installed")
    else:
        inter, raw = path_stack.run_gloss("空越えていく")
        del raw
        if "cross" not in inter and "sky" not in inter:
            fails.append(f"live gloss unexpected: {inter!r}")

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — chat wrap and gloss-to-path are structural")
    return 0


if __name__ == "__main__":
    sys.exit(run())
