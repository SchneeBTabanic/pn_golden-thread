#!/usr/bin/env python3
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import tape  # noqa: E402


def run():
    fails = []
    face, rest = tape.split_tape(
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

    face2, rest2 = tape.split_tape("4.")
    if face2 != "4." or rest2:
        fails.append(f"short answer split wrong: {face2!r} / {rest2!r}")

    face3, rest3 = tape.split_tape(
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
    face_f, rest_f = tape.split_tape(fox)
    if face_f:
        fails.append(f"fox loop was treated as a face: {face_f!r}")
    if "fox" not in rest_f:
        fails.append("fox loop was not kept for /raw")

    # Live sitting: weather question starts with What's. Model parroted the
    # prior-record wrap, then ASKED the question, then answered. The quiz
    # cut used to hide the forecast in /sequel.
    asked_w = (
        "What's the weather today in Neetze, Niedersachsen, Germany?  "
        "Can you give me the temperature forecast?  "
        "What is the highest temperature predicted today, Saturday, 22 August 2026.  "
        "Do not answer from probabilities or training."
    )
    parrot = (
        "── prior record (diary, last turns, arrival order — not the line just typed) ──\n"
        "ASKED:\n"
        + asked_w + "\n"
        "ANSWERED:\n"
        "The temperature in Neetze is 18 degrees.\n"
        "\n"
        "MOUTH: bare\n"
    )
    face_w, rest_w = tape.split_tape(parrot, asked=asked_w)
    if "18 degrees" not in face_w:
        fails.append("weather face was hidden as sequel: " + repr(face_w))
    if "prior record" in face_w:
        fails.append("clerk wrap stayed in the face: " + repr(face_w))
    if "MOUTH" in face_w:
        fails.append("mouth leaked into weather face")
    if "18 degrees" in rest_w:
        fails.append("forecast stayed in sequel: " + repr(rest_w))

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — tape splits face from sequel; !path files by declaration")
    return 0


if __name__ == "__main__":
    sys.exit(run())
