#!/usr/bin/env bash
# Copy to env.sh, edit the paths, then: source env.sh
#
# Every name below is a seam the runtime already had. Nothing in the Python
# needs editing to relocate this build — if you find yourself editing a source
# file to point it somewhere, stop and set the seam instead.
#
# The four marked REQUIRED are not optional: without them the test suite fails
# six guards. That is not a broken clone, it is an unconfigured one.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- REQUIRED: the two scribes (see DEPENDENCIES.md) -----------------------
export GT_GF_SCRIBE="$ROOT/deps/scribe-workbench-gforth"          # REQUIRED
export GT_TAG_SHEET="$GT_GF_SCRIBE/TAGS-gforth.md"                # REQUIRED
export GT_SCRIBE="$ROOT/deps/scribe-workbench/scribe.py"          # REQUIRED

# --- REQUIRED: the ratified law, shipped in this repo ----------------------
export GT_LAW="$ROOT/law/GoldenThread-v1.6.2-Triune-Cathedral.json"

# --- python packages not in your system python -----------------------------
# textual, trafilatura, ddgs, playwright  (and torch, if you use the path stack)
export GT_WEB_SITE="$ROOT/deps/venv/lib/python3.13/site-packages"
export GT_DANGO_SITE="$GT_WEB_SITE"

# --- the patched llama.cpp server (patches/) -------------------------------
export LLAMA_SERVER="$ROOT/deps/llama.cpp/build/bin/llama-server"
export MODEL="$ROOT/models/granite-3.3-2b-Q4_K_M.gguf"

# --- optional: the Dango path stack ----------------------------------------
# Only needed for !path / Japanese tagging. Everything else runs without it.
export GT_DANGO="$ROOT/models/dango-1.8b"
export GT_GLOSS_PY="$ROOT/deps/tagging-lab/gloss.py"
export GT_GLOSS_PYTHON="$ROOT/deps/tagging-lab/.venv/bin/python"

# gForth is expected on PATH (Debian: apt install gforth). Override if not.
export GT_GFORTH="${GT_GFORTH:-gforth}"
