# golden-thread

Thin local runtime. You talk to a local model. The answer prints first,
whole, on stdout. Python stamps what can be decided without interpretation,
on stderr. Each turn is captured into a scribe pile.

Not GTPS-Agent. Not Vessel. Does not retrieve, rank, embed, or inject the
48 clauses. `file:` places a file you named, whole, or refuses.

This tree has no lab-machine paths. A clone on a new disk works if you
follow the block below **while you still have a network**, then you can
run offline.

## One online day — fetch everything you will need offline

You need **this repo plus the gForth scribe**, gForth itself, a **pinned**
llama.cpp, a Granite GGUF, and a Python venv. Latest llama.cpp will not
do. The Python scribe is not required for talk.

```sh
# 1. trees
git clone git@github.com:SchneeBTabanic/pn_golden-thread.git
cd pn_golden-thread
mkdir -p deps models
git clone git@github.com:SchneeBTabanic/scribe-workbench-gforth.git deps/scribe-workbench-gforth

# 2. system
sudo apt install gforth pandoc poppler-utils build-essential cmake python3-venv python3-pip
# GPU build also needs your CUDA toolkit. CPU-only: skip CUDA.

# 3. Python (talk TUI + url:/search:). Not torch — that is optional Dango.
python3 -m venv deps/venv
deps/venv/bin/pip install -r requirements.txt
# optional JS-only pages:
# deps/venv/bin/python -m playwright install chromium

# 4. engine — pin b8461, NOT latest. Patch then COPY the two new units.
git clone https://github.com/ggml-org/llama.cpp.git deps/llama.cpp
cd deps/llama.cpp && git checkout cea560f4
git apply ../../patches/llama.cpp-b8461-gt-relied.patch
cp ../../llama-hook/gt-relied.cpp ../../llama-hook/gt-relied.h tools/server/
# GPU:
cmake -B build -DGGML_CUDA=ON && cmake --build build -j --target llama-server
# CPU-only, instead:
# cmake -B build && cmake --build build -j --target llama-server
cd ../..

# 5. a Granite 3.3 GGUF (2B Q4_K_M is enough to talk; 8B if you have VRAM)
#    ibm-granite on HuggingFace; put the file in models/ and name it in env.sh
```

Skip `git apply` + copy and you get a stock server: talk works, RELIED
is a named refusal.

## Then, on the machine that will run it (can be offline)

```sh
cp env.example.sh env.sh    # edit MODEL, and NGL=0 if CPU-only
source env.sh
python3 run_tests.py        # no model, no server — fails by name if a seam is missing
./scripts/run_llama_server.sh
python3 run.py
```

`run_llama_server.sh` **requires** `LLAMA_SERVER` and `MODEL`. It passes
`-fa off`. If flash attention stays on, talk still works; every RELIED
reading is a named refusal (`saw_softmax` never becomes true).

The clause file ships at `law/GoldenThread-v1.6.2-Triune-Cathedral.json`
(inoculated 2026-08-16; filename unchanged). `law.py` loads that file
when `GT_LAW` is unset. Default: not placed. `/withlaw` places the whole
file.

Packages, seams, and optional Dango: `DEPENDENCIES.md`.

## What a clone will not have until you fetch it

These are not in git. Miss them and the tree refuses by name, or talk
works without RELIED — it does not silently use another machine's paths.

1. **A Granite 3.3 GGUF is not in this repo.** On the online day download
   one (2B Q4_K_M is enough to talk; 8B if you have VRAM), put it in
   `models/`, set `MODEL=` in `env.sh`. The launch script exits if this
   is unset.
2. **CUDA is not an apt package here.** GPU build needs the toolkit you
   actually have. CPU-only: cmake without `-DGGML_CUDA=ON`, and `NGL=0`
   in `env.sh`.
3. **`LLAMA_SERVER` and `MODEL` have no lab default.** Copy
   `env.example.sh` to `env.sh` and source it. A leftover path from
   another disk will not be guessed.
4. **Flash attention must be off** (`-fa off`, already in the launch
   script). If you start `llama-server` by hand and leave FA on, talk
   still works; every RELIED reading is a named refusal.
5. **The gForth scribe is a second clone**, not vendored. Talk piles
   need `GT_GF_SCRIBE` and `GT_TAG_SHEET` pointing at
   `scribe-workbench-gforth` (`TAGS-gforth.md` is working input). The
   Python scribe is only for HTML `url:` reduction; talk does not need
   it.

A second CPU `llama-server` on `:8081` is this lab's sheet path, not
part of the clone. One patched binary from the block above is enough.
