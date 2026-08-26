#!/usr/bin/env python3
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import tape  # noqa: E402


def run():
    fails = []
    face, rest, bound = tape.split_tape(
        "Yes, Rudolf Steiner founded Anthroposophy.\n"
        "\n"
        "MOUTH: bare\n"
        "FETCHED: (nothing)\n"
        "\n"
        "What is the capital of Brazil?\n"
        "The capital of Brazil is Brasília.\n"
    )
    if "Steiner" not in face:
        fails.append(f"lost the face: {face!r}")
    if "MOUTH" in face or "Brazil" in face:
        fails.append(f"quiz stayed in the face: {face!r}")
    if "Brazil" not in rest:
        fails.append(f"sequel lost the quiz: {rest!r}")

    face2, rest2, _b2 = tape.split_tape("4.")
    if face2 != "4." or rest2:
        fails.append(f"short answer split wrong: {face2!r} / {rest2!r}")

    face3, rest3, _b3 = tape.split_tape(
        "Steiner was an Austrian philosopher.\n"
        "What is the difference between a meteor and a meteorite?\n"
        "A meteoroid is a small particle.\n"
    )
    if "Austrian" not in face3:
        fails.append(f"no-mouth face lost: {face3!r}")
    if "meteor" not in rest3:
        fails.append(f"no-mouth sequel lost: {rest3!r}")

    decl, raw = tape.parse_bang_path(
        "check the oven !path look in the venv first")
    if "venv" not in decl:
        fails.append(f"!path not taken: {decl!r}")
    if raw != "check the oven !path look in the venv first":
        fails.append("!path must not rewrite the message")

    if tape.should_file_sequel("Brasília is the capital.", ""):
        fails.append("undeclared tail must not be filed")
    if not tape.should_file_sequel("Brasília is the capital.",
                                   "look in the venv first"):
        fails.append("declared tail must be filed even with no word overlap")
    if not tape.should_file_sequel("I looked in the venv.",
                                   "look in the venv first"):
        fails.append("declared tail should be filed")
    if hasattr(tape, "sequel_on_path"):
        fails.append("sequel_on_path must not remain — substring is not meaning")

    fox = (
        "# Input:\n"
        "The quick brown fox jumps over the lazy dog\n"
        "\n"
        "# Output:\n"
        "Hello\n"
        "\n"
        "# Input:\n"
        "The quick brown fox jumps over the lazy dog\n"
    )
    face_f, rest_f, _bf = tape.split_tape(fox)
    if face_f:
        fails.append(f"fox loop was treated as a face: {face_f!r}")
    if "fox" not in rest_f:
        fails.append("fox loop was not kept for /raw")
    if _bf != 0:
        fails.append("fox cut_byte must be 0, got " + repr(_bf))

    # R4: peel/echo gone. A clean-born face keeps the forecast; a later
    # quiz still sequels. cut_byte is a UTF-8 prefix of unstripped raw.
    clean = (
        "The temperature in Neetze is 18 degrees.\n"
        "\n"
        "What is the capital of Brazil?\n"
        "The capital of Brazil is Brasília.\n"
    )
    face_w, rest_w, bound_w = tape.split_tape(clean)
    if "18 degrees" not in face_w:
        fails.append("clean weather face lost: " + repr(face_w))
    if "Brazil" in face_w:
        fails.append("quiz stayed in clean face: " + repr(face_w))
    if "Brazil" not in rest_w:
        fails.append("quiz lost from sequel")
    raw_b = clean.encode("utf-8")
    if bound_w is None or bound_w < 0 or bound_w > len(raw_b):
        fails.append("cut_byte not a prefix offset: " + repr(bound_w))
    if raw_b[:bound_w] + raw_b[bound_w:] != raw_b:
        fails.append("cut_byte does not split raw")
    if not raw_b[bound_w:].decode("utf-8").lstrip().startswith("What "):
        fails.append("cut_byte does not land on the quiz")
    if bound is None:
        fails.append("Steiner cut_byte still None")
    for gone in ("_peel_chrome", "is_echo_of_asked", "is_clerk_chrome"):
        if hasattr(tape, gone):
            fails.append("R4 left " + gone)

    mode, rest = tape.parse_score_place("^ Hello")
    if mode != "fold" or rest != "Hello":
        fails.append("caret fold drifted: " + repr((mode, rest)))
    mode, rest = tape.parse_score_place("^^ Hello")
    if mode != "raw" or rest != "Hello":
        fails.append("caret raw drifted: " + repr((mode, rest)))
    mode, rest = tape.parse_score_place("Hello^there")
    if mode is not None or rest != "Hello^there":
        fails.append("glued caret was taken: " + repr((mode, rest)))
    mode, rest = tape.parse_score_place("Hello")
    if mode is not None or rest != "Hello":
        fails.append("bare Hello grew a sigil: " + repr((mode, rest)))

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — tape splits face from sequel; !path files by declaration")
    return 0


if __name__ == "__main__":
    sys.exit(run())
