#!/usr/bin/env bash
# Copy to env.sh, edit the paths, then: source env.sh
#
# Every name below is a seam the runtime already had. Nothing in the Python
# needs editing to relocate this build — if you find yourself editing a source
# file to point it somewhere, stop and set the seam instead.
#
# The seams marked REQUIRED are not optional: without them the test suite
# fails named guards. That is not a broken clone, it is an unconfigured one.

export ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- REQUIRED: the gForth scribe (see DEPENDENCIES.md) ---------------------
export GT_GF_SCRIBE="$ROOT/deps/scribe-workbench-gforth"          # REQUIRED
export GT_TAG_SHEET="$GT_GF_SCRIBE/TAGS-gforth.md"                # REQUIRED

# Optional: Python scribe, only for HTML url: reduction (capture_html).
# Talk piles are gForth. Leave unset if you did not clone scribe-workbench.
# export GT_SCRIBE="$ROOT/deps/scribe-workbench/scribe.py"

# --- REQUIRED: the ratified law, shipped in this repo ----------------------
export GT_LAW="$ROOT/law/GoldenThread-v1.6.2-Triune-Cathedral.json"

# --- python packages (python3 -m venv deps/venv && pip install -r requirements.txt)
if [[ -x "$ROOT/deps/venv/bin/python" ]]; then
  export GT_WEB_SITE="$("$ROOT/deps/venv/bin/python" -c 'import sysconfig; print(sysconfig.get_path("purelib"))')"
else
  echo "env.sh: deps/venv is missing. python3 -m venv deps/venv && deps/venv/bin/pip install -r requirements.txt" >&2
fi

# --- the patched llama.cpp server (patches/ + llama-hook/) -----------------
export LLAMA_SERVER="$ROOT/deps/llama.cpp/build/bin/llama-server"
# Face GGUF (:8080 talk). 8B if you have a GPU. 2B is enough to talk on CPU.
export MODEL="$ROOT/models/granite-3.3-8b-Q4_K_M.gguf"
# Beneath GGUF (:8081 sheet/bind/LOOK/hop). Second process. 2B on CPU so it
# does not fight the 8B for VRAM. llama.cpp's job on CPU is system RAM.
export MODEL_BENEATH="$ROOT/models/granite-3.3-2b-Q4_K_M.gguf"
# If LLAMA_SERVER is CUDA-linked and the 8B already fills VRAM, NGL=0
# on that same binary is not isolation. Point this at a GGML_CUDA=OFF
# build (cmake without -DGGML_CUDA=ON). The launch script uses it when
# PORT=8081. --device none is a fallback, not the named solve.
# export LLAMA_SERVER_BENEATH="$ROOT/deps/llama.cpp-cpu/build/bin/llama-server"
export GT_LLAMA="http://127.0.0.1:8080"
export GT_WALK="http://127.0.0.1:8081"
# Optional: /keep refuses until bind has spoken.
# export GT_BIND_REQUIRED=1

# NGL is GPU *layers*, not conversation memory. 99 = offload to VRAM (face).
# Beneath launch uses NGL=0 (CPU / system RAM). Do not put both on the GPU
# when the 8B already fills VRAM.
export NGL="${NGL:-99}"
# Last-N / thread memory is GT_SCORE_HISTORY. Unset = raw (talk default).
# Do not export GT_SCORE_HISTORY=none unless you mean lab isolation.

# --- /walk Japanese (Dango). Face talk can start without it; /walk cannot.
# Dango is torch+transformers in-process, not llama.cpp. The talk venv from
# requirements.txt has no torch. Point GT_DANGO_SITE at a site-packages that
# actually contains torch, or /walk names the refusal and talk still works.
# export GT_DANGO_SITE="$GT_WEB_SITE"   # only if you pip install torch there
export GT_DANGO="$ROOT/models/dango-1.8b"
# Real Leipzig glosser, shipped in this repo (not ontology-midwife).
# Needs sudachipy + sudachidict_core in the talk venv. Do not stub this file.
export GT_GLOSS_PY="$ROOT/tagging-lab/gloss.py"
export GT_GLOSS_PYTHON="$ROOT/deps/venv/bin/python"

# gForth is expected on PATH (Debian: apt install gforth). Override if not.
export GT_GFORTH="${GT_GFORTH:-gforth}"
