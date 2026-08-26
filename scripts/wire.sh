#!/usr/bin/env bash
# After you have cloned the trees, built llama-server, and put a GGUF in
# models/: this script copies env.example.sh to env.sh if needed and names
# what is still missing. It does not download, compile, or guess a lab path.
#
#   ./scripts/wire.sh
#   source env.sh
#
# CPU-only build: NGL=0 ./scripts/wire.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

if [[ ! -f env.example.sh ]]; then
  echo "env.example.sh is missing from $HERE" >&2
  exit 2
fi

if [[ ! -f env.sh ]]; then
  cp env.example.sh env.sh
  echo "wrote env.sh from env.example.sh"
else
  echo "env.sh already exists — not overwritten"
fi

# shellcheck disable=SC1091
source "$HERE/env.sh"

missing=0
need() {
  local label="$1" path="$2"
  if [[ -e "$path" ]]; then
    echo "OK     $label"
    echo "       $path"
  else
    echo "MISSING  $label"
    echo "         expected: $path"
    missing=1
  fi
}

echo
echo "checking seams from env.sh (ROOT=$ROOT)"
need "gForth scribe directory" "${GT_GF_SCRIBE:-}"
need "tag sheet TAGS-gforth.md" "${GT_TAG_SHEET:-}"
need "clause file" "${GT_LAW:-}"
need "patched llama-server" "${LLAMA_SERVER:-}"
need "face GGUF (MODEL)" "${MODEL:-}"

if [[ -n "${MODEL:-}" && ! -f "${MODEL:-}" ]]; then
  echo
  echo "GGUF files already in models/ (set MODEL= in env.sh to one of these):"
  shopt -s nullglob
  ggufs=(models/*.gguf)
  if [[ ${#ggufs[@]} -eq 0 ]]; then
    echo "  (none — download a Granite 3.3 GGUF into models/)"
  else
    for g in "${ggufs[@]}"; do
      echo "  $HERE/$g"
    done
  fi
fi

if ! command -v gforth >/dev/null 2>&1; then
  echo "MISSING  gforth on PATH  (sudo apt install gforth)"
  missing=1
else
  echo "OK     gforth  $(command -v gforth)"
fi

if [[ ! -d "${GT_WEB_SITE:-}" ]]; then
  echo "MISSING  Python venv site-packages"
  echo "         python3 -m venv deps/venv && deps/venv/bin/pip install -r requirements.txt"
  missing=1
else
  echo "OK     GT_WEB_SITE"
  echo "       $GT_WEB_SITE"
fi

# /walk hop — talk can start without these; /walk cannot
if [[ -f "${GT_GLOSS_PY:-}" ]]; then
  echo "OK     gloss.py (Leipzig — middle of /walk, not a display extra)"
  echo "       $GT_GLOSS_PY"
else
  echo "WALK    gloss.py missing — /walk will refuse. Talk and /sheet still run."
  echo "         expected: ${GT_GLOSS_PY:-$HERE/tagging-lab/gloss.py}"
  echo "         do not stub this file; it ships in tagging-lab/"
fi
if [[ -d "${GT_DANGO:-}" ]]; then
  echo "OK     Dango weights"
  echo "       $GT_DANGO"
else
  echo "WALK    Dango weights missing — /walk will refuse. Talk and /sheet still run."
  echo "         expected: ${GT_DANGO:-$HERE/models/dango-1.8b}"
fi

echo
if [[ "$missing" -ne 0 ]]; then
  echo "Not ready. Fetch what is MISSING, edit MODEL= in env.sh if the GGUF"
  echo "filename differs, then:  source env.sh"
  echo "CPU-only: add  export NGL=0  to env.sh (both servers)."
  echo "8B face on GPU: leave NGL=99 for :8080; beneath is NGL=0."
  exit 1
fi

echo "Ready. In every new terminal:"
echo "  source $HERE/env.sh"
echo "Face (:8080, MODEL, NGL from env.sh):"
echo "  ./scripts/run_llama_server.sh"
echo "Beneath (:8081, 2B, CPU — NGL=0 on a CUDA binary is not isolation):"
echo "  NGL=0 PORT=8081 CTX=8192 MODEL=\"\$MODEL_BENEATH\" ./scripts/run_llama_server.sh"
echo "  (set LLAMA_SERVER_BENEATH to a GGML_CUDA=OFF binary if the 8B filled VRAM)"
echo "Talk (client, not a third server; do not set GT_SCORE_HISTORY=none):"
echo "  python3 run.py"
exit 0
