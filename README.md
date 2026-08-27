# golden-thread

Thin local runtime. You talk to a local model. The answer prints first,
whole, on stdout. Python stamps what can be decided without interpretation,
on stderr. Each turn is captured into a scribe pile.

Not GTPS-Agent. Not Vessel. Does not retrieve, rank, embed, or inject the
48 clauses. `file:` places a file you named, or refuses. If the file
fits the byte cap but not `n_ctx`, a **document-order prefix** is
placed and dropped paragraphs are named. Not a relevance pick.

This tree has no lab-machine paths. A clone on a new disk works if you
follow the block below **while you still have a network**, then you can
run offline.

## One online day — fetch everything you will need offline

You need **this repo plus the gForth scribe**, gForth itself, a **pinned**
llama.cpp, a Granite GGUF, and a Python venv. Latest llama.cpp will not
do. The Python scribe is not required for talk.

```sh
# 1. trees  (https — no GitHub account, no SSH key)
git clone https://github.com/SchneeBTabanic/pn_golden-thread.git
cd pn_golden-thread
mkdir -p deps models
git clone https://github.com/SchneeBTabanic/scribe-workbench-gforth.git deps/scribe-workbench-gforth

# 2. system
sudo apt install gforth pandoc poppler-utils build-essential cmake python3-venv python3-pip
# GPU build also needs your CUDA toolkit. CPU-only: skip CUDA.

# 3. Python (talk TUI + url:/search:). Torch is extra: /walk (Dango).
python3 -m venv deps/venv
deps/venv/bin/pip install -r requirements.txt
# optional JS-only pages:
# deps/venv/bin/python -m playwright install chromium

# 4. engine — pin b8461, NOT latest. Patch then COPY the two new units.
git clone https://github.com/ggml-org/llama.cpp.git deps/llama.cpp
cd deps/llama.cpp && git checkout cea560f4
git apply ../../patches/llama.cpp-b8461-gt-relied.patch
cp ../../llama-hook/gt-relied.cpp ../../llama-hook/gt-relied.h tools/server/
# GPU (NVIDIA, not a typical VM):
cmake -B build -DGGML_CUDA=ON && cmake --build build -j --target llama-server
# CPU-only (no GPU, or a VM that does not pass one through):
# cmake -B build && cmake --build build -j --target llama-server
cd ../..

# 5. a Granite 3.3 GGUF (2B Q4_K_M is enough to talk; 8B if you have VRAM)
#    ibm-granite on HuggingFace; put the file in models/ and name it in env.sh
#
# /walk (Dango) — HuggingFace safetensors, not a GGUF. Verb-path reveal.
#    Some huggingface_hub builds have no `python -m huggingface_hub download`
#    entry. snapshot_download always works:
#    deps/venv/bin/pip install huggingface_hub
#    deps/venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('mattashiho/dango-1.8b-100Btok', local_dir='models/dango-1.8b')"
```

Skip `git apply` + copy and you get a stock server: talk works, RELIED
is a named refusal.

## Then, on the machine that will run it (can be offline)

`env.sh` is a list of paths on **this** disk. You do not invent names.
Copy the example, then change only what is true of your files:

```sh
cp env.example.sh env.sh
# Open env.sh. MODEL= is the face GGUF (8B if you have VRAM).
# MODEL_BENEATH= is the 2B for :8081. NGL is GPU layers, not last-N.
./scripts/wire.sh           # names what is still MISSING; does not download
source env.sh               # load those paths into this terminal
python3 run_tests.py        # no model, no server — fails by name if a seam is missing
./scripts/run_llama_server.sh
# second terminal — beneath. CPU. Different GGUF and, if the face
# is a CUDA 8B filling VRAM, a CPU-only llama-server binary
# (LLAMA_SERVER_BENEATH). NGL=0 on the CUDA binary is not isolation.
source env.sh
NGL=0 PORT=8081 CTX=8192 MODEL="$MODEL_BENEATH" ./scripts/run_llama_server.sh
python3 run.py
```

Every new terminal needs `source env.sh` again. `wire.sh` will not overwrite
an `env.sh` you already edited.

Clone with **https** (`git clone https://github.com/….git`). You do not need
SSH, a GitHub account, or anyone else's key.

### What `env.sh` is

A list of paths on **this** disk. The other `export` lines already point
inside the clone (`deps/`, `law/`, `models/`). You do not invent those
names. After `cp env.example.sh env.sh`, open `env.sh` and change only
what is true of your files:

| Line | When to touch it |
|---|---|
| `MODEL=` | Face GGUF (`:8080`). 8B if you have VRAM; 2B is enough to talk on CPU. |
| `MODEL_BENEATH=` | 2B GGUF for `:8081`. Do not reuse the 8B here. |
| `NGL` | GPU *layers* for the face launch. Not conversation memory. `99` = VRAM; `0` = CPU / system RAM. |

Then `source env.sh` so this terminal can see those paths.

### What `./scripts/wire.sh` prints — expected, not a crash

It copies the example to `env.sh` if you have not yet, then checks each
path. **MISSING is the script doing its job.** Fetch that part, run
`wire.sh` again.

If a part is not there yet:

```
wrote env.sh from env.example.sh          (first run only)

checking seams from env.sh (ROOT=/path/to/pn_golden-thread)
OK     gForth scribe directory
       /path/to/pn_golden-thread/deps/scribe-workbench-gforth
MISSING  face GGUF (MODEL)
         expected: /path/to/pn_golden-thread/models/granite-3.3-2b-Q4_K_M.gguf

GGUF files already in models/ (set MODEL= in env.sh to one of these):
  (none — download a Granite 3.3 GGUF into models/)
MISSING  gforth on PATH  (sudo apt install gforth)
MISSING  Python venv site-packages
         python3 -m venv deps/venv && deps/venv/bin/pip install -r requirements.txt

Not ready. Fetch what is MISSING, edit MODEL= in env.sh if the GGUF
filename differs, then:  source env.sh
CPU-only: add  export NGL=0  to env.sh
```

If a GGUF is in `models/` under another name, that middle block lists
the real files instead of `(none — …)`. Put that path on the `MODEL=`
line.

When everything is present:

```
Ready. In every new terminal:
  source /path/to/pn_golden-thread/env.sh
Face:
  ./scripts/run_llama_server.sh
Beneath (/sheet, bind, LOOK, hop) — second terminal, CPU:
  NGL=0 PORT=8081 CTX=8192 MODEL="$MODEL_BENEATH" ./scripts/run_llama_server.sh
Talk:
  python3 run.py
```

If the face is 8B on a GPU, **do not** put the 2B on VRAM as well.
`NGL=0` on a **CUDA-linked** `llama-server` is not isolation: weights
stay in RAM, then the process still inits CUDA and OOM/segfaults on
leftover VRAM (compute buffers). The named solve is a **second
binary** built with `GGML_CUDA` off (`cmake -B build` with no
`-DGGML_CUDA=ON`). Set `LLAMA_SERVER_BENEATH` to that binary; the
launch script uses it when `PORT=8081`. `--device none` (added when
`NGL=0`) is a fallback on the CUDA binary, not the isolation the
sheet sitting named.

`NGL` is not last-N. Last-N is `GT_SCORE_HISTORY` (unset = `raw`, a
thread). `GT_SCORE_HISTORY=none` is lab isolation; do not set it for
talk.

`file:` / `url:` / `html:` fill the face window in **document order**.
`GT_FILE_MAX_BYTES` is a read cap. What enters Granite is a prefix that
still leaves room for `n_predict` inside `n_ctx`. If the first
paragraph is itself larger than that remainder, a prefix of it is
placed (lines, then sentences, then characters) and the remainder is
named (`DROPPED: remainder of paragraph 1 after a document-order …
prefix`). Not a relevance pick.

A box with no GPU: `NGL=0` on **both** servers. The 2B at `:8081`
still needs `-c 8192` so the **whole** `TAGS-gforth.md` fits. A
live-core is not the sheet; this summons will not amputate it.

`/sheet` uses that 2B twice: first it proposes `@act` / `@path` lines, then
it **binds** — ordinary sentences asking whether those lines still name a
doing *in this face answer*, or are clothing. Shown, not filed. `/bind`
re-runs only the second pass. `/keep` files the proposal you judged and
files the bind speech (or names that bind was silent). Python does not
score the bind. `!path` LOOK also POSTs to `:8081`, not the face.

`run_llama_server.sh` **requires** `LLAMA_SERVER` and `MODEL`. It passes
`-fa off`. If flash attention stays on, talk still works; every RELIED
reading is a named refusal (`saw_softmax` never becomes true).

The clause file ships at `law/GoldenThread-v1.6.2-Triune-Cathedral.json`
(inoculated 2026-08-16; filename unchanged). `law.py` loads that file
when `GT_LAW` is unset. Default: not placed. `/withlaw` places the whole
file.

Packages and seams: `DEPENDENCIES.md`. `@act` / `@path` are the living
core (Talmy verb-path). Dango is how `/walk` *reveals* that in Japanese;
the face can talk without it, but then that reveal is a named absence.

How to move inside a sitting (posture, commands, bind, speculative
trajectory): `GUIDE_pn_golden-thread.md`. Setup stays here. The tag lab
stays in `scribe-workbench-gforth`.

## What a clone will not have until you fetch it

These are not in git. Miss them and the tree refuses by name, or talk
works without RELIED — it does not silently use another machine's paths.

1. **A Granite 3.3 GGUF is not in this repo.** On the online day download
   one (2B Q4_K_M is enough to talk; 8B if you have VRAM), put it in
   `models/`, set `MODEL=` in `env.sh`. The launch script exits if this
   is unset.
2. **A GPU is not required for talk, and RELIED is not GPU-only math.**
   RELIED is a **patch** in llama.cpp that reads attention softmax
   (`kq_soft_max`) while the model decodes. That needs the patched
   `llama-server` and **`-fa off`**. It does **not** need CUDA. A stock
   server talks; it cannot emit RELIED. Flash attention on (even on GPU)
   makes every RELIED reading a named refusal.

   A VM usually has **no GPU passthrough** unless someone configured it.
   That is normal. Use the CPU cmake line and `NGL=0` on both servers.
   If the face *is* 8B on GPU (`NGL=99` at `:8080`), run the 2B
   beneath at `:8081` with `NGL=0` (system RAM). Two GGUFs on one GPU
   is how VRAM dies. Granite **2B** Q4_K_M is enough for beneath on
   CPU. 8B on CPU is possible and slow. 8B on GPU is speed and VRAM,
   not a RELIED requirement.
3. **`LLAMA_SERVER` and `MODEL` have no lab default.** Copy
   `env.example.sh` to `env.sh` and source it. A leftover path from
   another disk will not be guessed.
4. **Flash attention must be off** (`-fa off`, already in the launch
   script). If you start `llama-server` by hand and leave FA on, talk
   still works; every RELIED reading is a named refusal.
5. **The gForth scribe is a second clone**, not vendored. Talk piles
   need `GT_GF_SCRIBE` and `GT_TAG_SHEET` pointing at
   `scribe-workbench-gforth`. `TAGS-gforth.md` **is** the `/sheet` list —
   working input, not docs. `/sheet` in `run.py` hands that whole file to
   the 2B at `:8081`. Cloning the scribe without starting that second
   server means `/sheet` refuses by name (`No beneath server at …:8081`).
   Same patched `llama-server` binary, second process, 2B GGUF,
   `-c 8192`, `NGL=0` (CPU) if the face is already on the GPU.
   The Python scribe is only for HTML `url:` reduction; talk does not need
   it.
6. **`/walk` (Dango) is not llama.cpp, and it is not a toy extra.**
   `@act` (a doing) and `@path` (a reaching) are how a turn stays
   *living* in the pile — Talmy’s verb-path, the same hop Namirha has
   been working. Dango is the Japanese mouth of that hop: English hides
   the verb in a noun-bucket; Japanese makes it harder. `/sheet` + bind
   on the 2B still use the tag sheet without Dango. **Talk can start
   without Dango.** A sitting that never `/walk`s has skipped the
   reveal, not discovered that verb-path does not matter. If Dango is
   unset, `/walk` refuses by name.

You do **not** start the program with `source deps/venv/bin/activate`.
Startup is still:

```sh
source env.sh
python3 run.py
```

That `python3` is your normal system Python. Nothing “runs the venv” as a
second program.

The venv is a **box of libraries**, not a second engine. `env.sh` points
`GT_WEB_SITE` (TUI) and `GT_DANGO_SITE` (Dango) at that box’s
`site-packages` folder. When `/walk` needs Dango, **the same** `run.py`
process puts that folder on its import path and loads torch **inside
itself**. No second server, no second Python.

Talk’s `requirements.txt` venv is enough for the TUI. `/walk` needs extra
packages in that same box. On Debian/Ubuntu:

```sh
# still in the clone directory, after step 3
deps/venv/bin/pip install torch transformers huggingface_hub
deps/venv/bin/pip install sudachipy sudachidict_core   # Leipzig gloss
```

`accelerate` is not required. The loader does not use `device_map`.

Then in `env.sh`:

```sh
export GT_DANGO_SITE="$GT_WEB_SITE"
```

`GT_WEB_SITE` is already set from `deps/venv` when that venv exists.
`source env.sh` again. Talk without `/walk` does not need torch. Weights:
`https://huggingface.co/mattashiho/dango-1.8b-100Btok` into
`models/dango-1.8b` (see `DEPENDENCIES.md`). If Dango still cannot
start, `/walk` prints why (missing weights, or still no torch). Talk
and `/sheet` work without this.

If `/walk` **refuses by name** (weights, torch, gloss), that is the
venv / path seam. Repair it, walk again.

`/walk` runs Option A in front of Dango on the **beneath** server
(`:8081`), not the talk face. Talk’s `:8080` slot still holds last-N
and ── divider chrome; a hop there continues the wrap. Beneath
translates (you will see `hop-asked` / `hop-answered`), Dango writes
the movement sentence, Leipzig glosses. If the hop is not Japanese,
`/walk` refuses and prints `hop-raw:`. Do not scrape ── off face
output. If Dango still prints no Japanese after a Japanese hop, read
`dango-raw:`.

The Leipzig glosser is `tagging-lab/gloss.py` in this repo, with
`jmdict-lemmas.tsv`. It is not in a private ontology-midwife tree. It
is the middle of `/walk`, not a display extra. Do not write a
passthrough stub so `/walk` “completes.” Missing Sudachi: `/walk`
refuses by name. Talk and `/sheet` still run. Do not swap Dango for an
instruct-tuned Japanese model.
