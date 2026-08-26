#!/usr/bin/env python3
"""Phase 4a: head profile loaded, never computed, never all-heads."""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import examine  # noqa: E402
import relied  # noqa: E402
import turn_record  # noqa: E402


HOLD_BANNER = (
    "[HELD — testimony placed by the human, in stasis. Not fact, not error.\n"
    "Do not adopt it. Do not argue it away. Answer from yourself.\n"
    "If your answer contradicts it, say so plainly and leave it held.\n"
    "It is released only by the human, never by an answer.]"
)


def run():
    fails = []
    if turn_record.HOLD_BANNER != HOLD_BANNER:
        fails.append("HOLD_BANNER was modified — it is not to be touched")
    if "RELIED says where attention mass went" not in open(
            os.path.join(HERE, "examine.py"), encoding="utf-8").read():
        fails.append("examine.py missing the RELIED reach comment")
    src = open(os.path.join(HERE, "model.py"), encoding="utf-8").read()
    if "PROBE_TEMPERATURE = 0.0" not in src:
        fails.append("PROBE_TEMPERATURE is not 0")
    if "seed=PROBE_SEED" not in src:
        fails.append("probe does not pass the fixed seed")
    if "temperature=PROBE_TEMPERATURE" not in src:
        fails.append("probe does not pass temperature 0")

    tmp = tempfile.mkdtemp(prefix="gt-relied-")
    old = os.environ.get("GT_HEADS_DIR")
    os.environ["GT_HEADS_DIR"] = tmp
    try:
        model_path = os.path.join(tmp, "fake.gguf")
        with open(model_path, "wb") as f:
            f.write(b"checkpoint-bytes-aaaa")
        digest = relied.file_sha256(model_path)
        if len(digest) != 64:
            fails.append("sha256 length drifted: " + repr(digest))

        if relied.load_profile(model_path) is not None:
            fails.append("missing profile was worn")
        line = relied.clock("llama", model_path)
        if line != relied.UNPROFILED:
            fails.append("unprofiled clock drifted: " + repr(line))
        if "all-heads" in line or "all heads" in line:
            fails.append("unprofiled line named all-heads")

        costume = relied.clock("ollama", model_path)
        if "costume" not in costume or "ollama" not in costume:
            fails.append("ollama costume drifted: " + repr(costume))
        if relied.load_profile(model_path) is not None:
            fails.append("ollama path invented a profile")

        other = os.path.join(tmp, "other.gguf")
        with open(other, "wb") as f:
            f.write(b"checkpoint-bytes-bbbb")
        other_sha = relied.file_sha256(other)
        worn = {
            "model_path": other,
            "sha256": other_sha,
            "heads": [[1, 2], [3, 4]],
            "method": "test",
            "date": "2026-08-20",
        }
        with open(os.path.join(tmp, "wrong.json"), "w", encoding="utf-8") as f:
            json.dump(worn, f)
        if relied.load_profile(model_path) is not None:
            fails.append("a swapped checkpoint wore another sha's profile")

        rec = {
            "model_path": model_path,
            "sha256": digest,
            "heads": [[16, 19], [11, 15]],
            "method": "niah-copy-score test",
            "date": "2026-08-20",
        }
        with open(os.path.join(tmp, digest + ".json"), "w", encoding="utf-8") as f:
            json.dump(rec, f)
        got = relied.load_profile(model_path)
        if got is None:
            fails.append("matching profile was not loaded")
        elif got["heads"] != [[16, 19], [11, 15]]:
            fails.append("heads drifted: " + repr(got["heads"]))
        elif got["sha256"] != digest:
            fails.append("loaded sha drifted")
        line = relied.clock("llama", model_path)
        if line != relied.NONE_PLACED:
            fails.append("profiled none-placed clock drifted: " + repr(line))
        masses = [("辻1016#42/1", 0.71), ("辻1016#57/2", 0.06)]
        lined = relied.clock("llama", model_path, masses=masses, placed=True)
        if "0.71" not in lined or "0.06" not in lined:
            fails.append("masses clock lost fractions: " + repr(lined))
        if relied.REACH_NOTE not in lined:
            fails.append("masses clock lost the reach note")
        if "  · " not in lined and " · " not in lined:
            fails.append("masses clock lost the middle-dot join")

        rec["heads"] = []
        with open(os.path.join(tmp, digest + ".json"), "w", encoding="utf-8") as f:
            json.dump(rec, f)
        got = relied.load_profile(model_path)
        if got is None or got["heads"]:
            fails.append("empty heads list was not loaded as empty")
        line = relied.clock("llama", model_path)
        if line != relied.NO_HEADS:
            fails.append("empty-heads clock drifted: " + repr(line))

        rec["heads"] = "all"
        with open(os.path.join(tmp, digest + ".json"), "w", encoding="utf-8") as f:
            json.dump(rec, f)
        if relied.load_profile(model_path) is not None:
            fails.append("heads:'all' was worn — that is the all-heads fallback")
        rec["heads"] = [[0, 1, 2]]
        with open(os.path.join(tmp, digest + ".json"), "w", encoding="utf-8") as f:
            json.dump(rec, f)
        if relied.load_profile(model_path) is not None:
            fails.append("malformed head triple was worn")
    except Exception as e:
        fails.append("exception: " + repr(e))
    finally:
        if old is None:
            os.environ.pop("GT_HEADS_DIR", None)
        else:
            os.environ["GT_HEADS_DIR"] = old
        shutil.rmtree(tmp, ignore_errors=True)

    if relied.fraction_mean(8.0, 4, 2) != 1.0:
        fails.append("fraction_mean 8/8 should be 1")
    if abs(relied.fraction_mean(3.0, 2, 2) - 0.75) > 1e-9:
        fails.append("fraction_mean 3/4 drifted")
    if relied.fraction_mean(1.0, 0, 4) != 0.0:
        fails.append("fraction_mean with 0 heads must be 0, not all-heads")
    got = relied.parse_gt_relied({"gt_relied": {"needle": 0.4}})
    if not got or got.get("needle") != 0.4:
        fails.append("parse_gt_relied lost needle")
    if relied.parse_gt_relied({"content": "4"}) is not None:
        fails.append("missing hook was treated as a fraction")
    prof = [[0, 26], [17, 6]]
    ctrl = relied.control_heads(prof, 40, 32, 2)
    if len(ctrl) != 2:
        fails.append("control set size drifted")
    if tuple(ctrl[0]) in {(0, 26), (17, 6)}:
        fails.append("control set overlapped the profile")

    def char_tok(s):
        return list(s or "")

    body = "UNIQUE-BODY-XYZ"
    full = "HEAD\n" + body + "\nTAIL"
    rng = relied.token_range(full, body, char_tok)
    if rng is None:
        fails.append("token_range missed a unique body")
    else:
        a, b = rng
        covered = "".join(char_tok(full)[a:b])
        if covered != body:
            fails.append("span did not exactly cover the body: " + repr(covered))
    if relied.ASKED_SPAN != "asked":
        fails.append("ASKED_SPAN drifted: " + repr(relied.ASKED_SPAN))
    twice = "Q?\nFILE quotes Q?\nQ?"
    first = relied.token_range(twice, "Q?", char_tok)
    last = relied.token_range_last(twice, "Q?", char_tok)
    if first is None or last is None:
        fails.append("asked span range missed")
    elif first == last:
        fails.append("token_range_last did not prefer the live line")
    elif last[0] <= first[0]:
        fails.append("last asked span was not after the first: "
                     + repr((first, last)))
    spans_first = relied.spans_for_hook(
        twice, [("asked", "Q?")], char_tok)
    spans_last = relied.spans_for_hook(
        twice, [("asked", "Q?")], char_tok, last_ids=("asked",))
    if not spans_first or not spans_last:
        fails.append("spans_for_hook missed asked")
    elif spans_first[0]["start"] == spans_last[0]["start"]:
        fails.append("last_ids did not move the asked span")
    run_src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if "relied.ASKED_SPAN" not in run_src:
        fails.append("face does not name the asked span")
    if "last_ids=asked_last" not in run_src:
        fails.append("asked span is not located at last occurrence")
    tag = relied.relied_tag_value("辻1016#42/99", 0.71)
    if " " in tag:
        fails.append("relied tag value has a space: " + tag)
    if tag != "辻1016#42/99-0.71":
        fails.append("relied tag value drifted: " + tag)
    if relied.clock("llama", "/no/such", masses=None, placed=False) != (
            relied.UNPROFILED):
        fails.append("missing model file must stay unprofiled")

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — profile loaded by sha; unprofiled named; never all-heads")
    return 0


if __name__ == "__main__":
    sys.exit(run())
