# What this runtime needs, and where to get it

**The working set is not this directory.** That is the single most useful fact
about this build. The code reaches outside itself in three different ways, and
each needs a different remedy. Telling them apart is most of the setup.

Everything below is reached through a `GT_*` environment seam that already
exists in the source. **You should never have to edit a Python file to relocate
this build.** If you find yourself doing that, set the seam instead.

Start from `env.example.sh`: copy it to `env.sh`, edit the paths, `source env.sh`.

---

## 1. The gForth scribe — REQUIRED

Talk piles are gForth format. Clone this repo; do not vendor it.

| Need | Repo | Seam |
|---|---|---|
| gForth scribe (the pile runtime) | `SchneeBTabanic/scribe-workbench-gforth` | `GT_GF_SCRIBE` |
| Tag sheet (read at runtime, not docs) | same repo, `TAGS-gforth.md` | `GT_TAG_SHEET` |

```sh
mkdir -p deps && cd deps
git clone https://github.com/SchneeBTabanic/scribe-workbench-gforth.git
```

`pile_io.py` shells to the gForth leaves `pn-keep.fs`, `pn-gread.fs`,
`pn-gindex.fs`. `path_stack.py` **reads** `TAGS-gforth.md` at runtime — it is
working input, not documentation, and an absent sheet is a named refusal.

The Python scribe (`SchneeBTabanic/scribe-workbench`, `GT_SCRIBE`) is **not**
required for talk. It is only `capture_html` / `loss_check` for HTML `url:`
reduction. An unset `GT_SCRIBE` is a named refusal on that path, not a broken
clone.

**Without `GT_GF_SCRIBE` and `GT_TAG_SHEET`, the suite fails named guards.**
That is an unconfigured clone, not a broken one.

## 2. gForth 0.7.3 — the interpreter

```sh
sudo apt install gforth          # Debian/Ubuntu: 0.7.3+dfsg-9
```

Upstream: <https://github.com/forthy42/gforth>. Expected on `PATH`; override
with `GT_GFORTH`. This is the language the pile runtime is written in, and it is
not interchangeable with the Python scribe — the two pile formats are not
mutually readable.

## 3. The patched llama.cpp server

**The patch is in this repo. It is not a promise.** `patches/` holds the exact
diff, and `llama-hook/` holds the two new translation units as standalone files.

```
upstream   github.com/ggml-org/llama.cpp
baseline   cea560f483f0f03e828a6c76e78821debdecbe06   (tag b8461)
patch      patches/llama.cpp-b8461-gt-relied.patch     (4 existing files in tools/server)
new files  copy llama-hook/gt-relied.cpp and gt-relied.h into tools/server/
```

The patch does not contain the two new units. `git apply` then `cp` from
`llama-hook/`, or cmake fails looking for files that are not there.

**Flash attention OFF at runtime.** `-fa off`. The default is `auto`, which
turns it on, and then the `kq_soft_max` tensors the hook reads do not exist:
`saw_softmax` stays false and every reading is a named refusal.
`scripts/run_llama_server.sh` passes `-fa off`.

The hook also emits a **per-token series** (`gt_relied_series`: `scale`,
`prefix_bytes`, `bytes`, per-span integer masses) alongside the single fraction.
That field is additive — the fraction is unchanged, so a reader that predates it
still works. `prefix_bytes` counts generation produced before the first measured
step: the first sampled token's logits come from the prompt decode, which the
hook skips, so it has bytes but no reading. Speculative decoding voids the
series rather than emitting a curve that would be quietly wrong.

```sh
mkdir -p deps && cd deps
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp && git checkout cea560f4
git apply ../../patches/llama.cpp-b8461-gt-relied.patch
cp ../../llama-hook/gt-relied.cpp ../../llama-hook/gt-relied.h tools/server/
cmake -B build -DGGML_CUDA=ON && cmake --build build -j --target llama-server
# no GPU / typical VM (no passthrough):
# cmake -B build && cmake --build build -j --target llama-server
# second binary for beneath when the CUDA 8B already fills VRAM:
# cmake -B build-cpu && cmake --build build-cpu -j --target llama-server
# then LLAMA_SERVER_BENEATH=.../build-cpu/bin/llama-server
```

RELIED is that patch plus `-fa off`. It is not a CUDA-only calculation.
CPU builds emit the same fields if the hook is compiled in. GPU is for
offload speed (8B). A VM without GPU access should use the CPU cmake
line. If the **face** is the CUDA 8B filling VRAM, beneath is a
**second** `GGML_CUDA=OFF` binary — `NGL=0` on the CUDA binary is not
isolation (compute buffers still hit leftover VRAM).

The patch adds the RELIED attention-mass hook to `tools/server/`. **You cannot
substitute an unpatched `llama-server`**: `relied.py` and
`scripts/validate_relied_gguf.py` read fields that stock builds do not emit.
Everything *else* in this runtime works against a stock server.

Point `LLAMA_SERVER` at the binary. It is not on `PATH` and Python will not find
it for you; `scripts/run_llama_server.sh` calls it by full path.

## 4. Python packages

Not in system Python. `requirements.txt` is the talk set. Put them in a venv
and point `GT_WEB_SITE` at its `site-packages` — the runtime inserts that on
`sys.path` rather than requiring you to run under that interpreter.
`env.example.sh` derives the path from `deps/venv/bin/python` so it does not
hardcode `python3.13`.

```
textual==8.2.8         the TUI (talk_tui.py)
trafilatura==2.0.0     HTML main-text reduction at the placement boundary
ddgs==9.11.3           search: — the hit list, nothing auto-fetched
playwright==1.58.0     JS-only pages; GT_EDGE_BROWSER=0 disables
rich                   pulled in by textual
torch==2.6.0           only for the Dango path stack and the 4a profiler
transformers==4.57.6   same — not in requirements.txt
sudachipy + dict       Leipzig gloss subprocess (`tagging-lab/gloss.py`)
huggingface_hub        Dango snapshot download (the `download` CLI may be absent)
```

```sh
python3 -m venv deps/venv
deps/venv/bin/pip install -r requirements.txt
deps/venv/bin/python -m playwright install chromium   # optional JS edge
```

## 5. System tools

```sh
sudo apt install pandoc poppler-utils
```

`strip.py` reduces HTML/PDF/docx/odt/epub at the boundary via `pandoc` and
`pdftotext`. A missing tool is a **named refusal**, never a silent partial page.

## 6. Models — not shipped, and large

| Model | Size | Seam | Needed for |
|---|---|---|---|
| `granite-3.3-2b-Q4_K_M.gguf` | 1.5 GB | `MODEL` | default engine |
| `granite-3.3-8b-Q4_K_M.gguf` | 4.9 GB | `MODEL` | the 8B path |
| `granite-3.3-8b-hf` | 16 GB | `--hf` | offline 4a profiler only |
| `dango-1.8b` | 3.5 GB | `GT_DANGO` | `/walk` Japanese reveal of `@act`/`@path` |

Granite GGUF from `ibm-granite` on HuggingFace; quantisations are widely
mirrored. **The 2B GGUF is enough for the face to talk.** That is boot,
not a statement that verb-path is extra.

Dango is **not** a GGUF and **not** llama.cpp. It is the `/walk` mouth:
Japanese so the doing is harder to hide. `@act` and `@path` are the
live core of the tag sheet (Talmy motion-event). Face talk can start
without Dango; `/walk` then refuses by name. `/sheet` and bind still
run on the 2B.
Checkpoint: <https://huggingface.co/mattashiho/dango-1.8b-100Btok>
(Shiho Matta et al.; code <https://github.com/mattashiho233/dango>).
Put the snapshot at `models/dango-1.8b` so `GT_DANGO` matches `env.example.sh`.
This is the specified Japanese organ. Do not swap it for an
instruction-tuned 1.8B.

```sh
# Some huggingface_hub versions have no `python -m huggingface_hub download`.
deps/venv/bin/pip install huggingface_hub
deps/venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('mattashiho/dango-1.8b-100Btok', local_dir='models/dango-1.8b')"
```

The Leipzig glosser ships at `tagging-lab/gloss.py` (SudachiPy + JMdict
lemma table). It is not a private ontology-midwife path. Install
`sudachipy` and `sudachidict_core` into `deps/venv`. Leipzig is the
middle of `/walk` (the stems are the shape of `@act` / `@path`). A
missing gloss: `/walk` refuses by name. Talk can start; `/walk` cannot.
Do not stub the file.

Default engine is `llama-server` at `:8080`. Ollama is a permitted client for
unmasked talk (`GT_OLLAMA`), not the architecture.

---

## Known rough edge

`scripts/validate_relied_gguf.py` reads `MODEL` or `GT_GGUF`. It is not on the
talk path. Ignore it until those are set.

## Not published

This repo is a **clean tree with no working history** — it carries the code, not
the build record. Deliberately absent, and named rather than pretended away:

- `piles/turns.pn`, `turns.txt`, `docs.txt`, `story.txt` — live session piles.
  `docs.txt` is regenerable: `python3 piles/_seed_docs.py` (needs `GT_SCRIBE`).
  Until you do, `show_docs.py` refuses by name, which is the intended behaviour.
- `tests/sovereign-test_terminal-output_*.txt`, `BRIEF_sovereign-test_*` —
  transcripts and findings briefs.
- `AGENTS.md`, `.grok/piles/*`, the Design Charter, `user-guide_*`,
  `GUIDE_derived_*`, and the old `GUIDE_*_for_Dummies` files. They are
  not in this tree. The posture guide that *is* published is
  `GUIDE_pn_golden-thread.md`.
