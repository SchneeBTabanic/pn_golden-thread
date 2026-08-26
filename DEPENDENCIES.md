# What this runtime needs, and where to get it

**The working set is not this directory.** That is the single most useful fact
about this build. The code reaches outside itself in three different ways, and
each needs a different remedy. Telling them apart is most of the setup.

Everything below is reached through a `GT_*` environment seam that already
exists in the source. **You should never have to edit a Python file to relocate
this build.** If you find yourself doing that, set the seam instead.

Start from `env.example.sh`: copy it to `env.sh`, edit the paths, `source env.sh`.

---

## 1. The two scribes — REQUIRED

Both are separate public repos. The runtime shells out to one and imports from
the other; neither is vendored here, because both are published in their own
right and duplicating them would create two copies of one truth.

| Need | Repo | Seam |
|---|---|---|
| gForth scribe (the pile runtime) | `SchneeBTabanic/scribe-workbench-gforth` | `GT_GF_SCRIBE` |
| Tag sheet (read at runtime, not docs) | same repo, `TAGS-gforth.md` | `GT_TAG_SHEET` |
| Python scribe (`capture_html`, `loss_check`) | `SchneeBTabanic/scribe-workbench` | `GT_SCRIBE` |

```sh
mkdir -p deps && cd deps
git clone git@github.com:SchneeBTabanic/scribe-workbench-gforth.git
git clone git@github.com:SchneeBTabanic/scribe-workbench.git
```

`pile_io.py` shells to the gForth leaves `pn-keep.fs`, `pn-gread.fs`,
`pn-gindex.fs`. `path_stack.py` **reads** `TAGS-gforth.md` at runtime — it is
working input, not documentation, and an absent sheet is a named refusal.

Only `capture_html` and `loss_check` are used from the Python scribe.

**Without these four seams set, the suite fails six guards.** That is an
unconfigured clone, not a broken one.

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
patch      patches/llama.cpp-b8461-gt-relied.patch     (4 files in tools/server)
new files  tools/server/gt-relied.cpp, gt-relied.h     (also in llama-hook/)
```

**Build it with flash attention OFF at runtime.** `-fa off`. The default is
`auto`, which turns it on, and then the `kq_soft_max` tensors the hook reads do
not exist: `saw_softmax` stays false and every reading is a named refusal.
`scripts/run_llama_server.sh` does not pass it.

The hook also emits a **per-token series** (`gt_relied_series`: `scale`,
`prefix_bytes`, `bytes`, per-span integer masses) alongside the single fraction.
That field is additive — the fraction is unchanged, so a reader that predates it
still works. `prefix_bytes` counts generation produced before the first measured
step: the first sampled token's logits come from the prompt decode, which the
hook skips, so it has bytes but no reading. Speculative decoding voids the
series rather than emitting a curve that would be quietly wrong.

```sh
cd deps && git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp && git checkout cea560f4
git apply ../../patches/llama.cpp-b8461-gt-relied.patch
cmake -B build -DGGML_CUDA=ON && cmake --build build -j --target llama-server
```

The patch adds the RELIED attention-mass hook to `tools/server/`. **You cannot
substitute an unpatched `llama-server`**: `relied.py` and
`scripts/validate_relied_gguf.py` read fields that stock builds do not emit.
Everything *else* in this runtime works against a stock server.

Point `LLAMA_SERVER` at the binary. It is not on `PATH` and Python will not find
it for you; `scripts/run_llama_server.sh` calls it by full path.

## 4. Python packages

Not in system Python. Put them in a venv and point `GT_WEB_SITE` at its
`site-packages` — the runtime inserts that on `sys.path` rather than requiring
you to run under that interpreter.

```
textual==8.2.8         the TUI (talk_tui.py)
trafilatura==2.0.0     HTML main-text reduction at the placement boundary
ddgs==9.11.3           search: — the hit list, nothing auto-fetched
playwright==1.58.0     JS-only pages; GT_EDGE_BROWSER=0 disables
rich                   pulled in by textual
torch==2.6.0           only for the Dango path stack and the 4a profiler
transformers==4.57.6   same
```

`playwright install chromium` for the browser, if you want the JS edge.

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
| `dango-1.8b` | 3.5 GB | `GT_DANGO` | `!path` Japanese tagging only |

Granite from `ibm-granite` on HuggingFace; GGUF quantisations are widely
mirrored. **Only the first is needed to talk.** The rest are optional paths.

Default engine is `llama-server` at `:8080`. Ollama is a permitted client for
unmasked talk (`GT_OLLAMA`), not the architecture.

---

## Known rough edge

`scripts/validate_relied_gguf.py` hardcodes its GGUF path with **no** env seam,
unlike every other path in the build. Edit line 24 or ignore that script. It is
recorded here rather than quietly patched, because the file is published exactly
as it runs.

## Not published

This repo is a **clean tree with no working history** — it carries the code, not
the build record. Deliberately absent, and named rather than pretended away:

- `piles/turns.pn`, `turns.txt`, `docs.txt`, `story.txt` — live session piles.
  `docs.txt` is regenerable: `python3 piles/_seed_docs.py` (needs `GT_SCRIBE`).
  Until you do, `show_docs.py` refuses by name, which is the intended behaviour.
- `tests/sovereign-test_terminal-output_*.txt`, `BRIEF_sovereign-test_*` —
  transcripts and findings briefs.
- `AGENTS.md`, `.grok/piles/*`, the Design Charter, `GUIDE_*`, `user-guide_*`,
  and `GUIDE_derived_*` files. They are not in this tree.
