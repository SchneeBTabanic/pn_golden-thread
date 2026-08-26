#!/usr/bin/env bash
# Start the llama.cpp server this runtime talks to.
#
# llama-server is a compiled binary at LLAMA_SERVER. It is not on PATH
# and it is not in this directory. Typing `llama-server` from here fails
# with "command not found". Claude Code's GTPS-Agent wrapper works for
# the same reason this one does: it calls the binary by full path.
# Working directory does not matter.
#
#   ./scripts/run_llama_server.sh
#   ./scripts/run_llama_server.sh -m /mnt/data/models/granite-3.3-8b-Q4_K_M.gguf --port 8080 -c 4096
#   MODEL=/mnt/data/models/granite-3.3-8b-Q4_K_M.gguf CTX=4096 ./scripts/run_llama_server.sh
#
# Env (a matching CLI flag wins when both are set):
#   LLAMA_SERVER  binary
#   MODEL         .gguf path
#   PORT          default 8080   (run.py looks here)
#   CTX           default 8192   (drop to 4096 for the 8B on 6 GB)
#   NGL           default 99     (full GPU offload)
set -euo pipefail

SERVER="${LLAMA_SERVER:-/mnt/data/Codeberg/llama_server_build/bin/llama-server}"
MODEL="${MODEL:-/mnt/data/models/granite-3.3-2b-Q4_K_M.gguf}"
PORT="${PORT:-8080}"
CTX="${CTX:-8192}"
NGL="${NGL:-99}"

EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--model)
      [[ $# -ge 2 ]] || { echo "$1 needs a .gguf path" >&2; exit 2; }
      MODEL="$2"; shift 2 ;;
    --port)
      [[ $# -ge 2 ]] || { echo "--port needs a number" >&2; exit 2; }
      PORT="$2"; shift 2 ;;
    -c|--ctx)
      [[ $# -ge 2 ]] || { echo "$1 needs a context size" >&2; exit 2; }
      CTX="$2"; shift 2 ;;
    -ngl)
      [[ $# -ge 2 ]] || { echo "-ngl needs a layer count" >&2; exit 2; }
      NGL="$2"; shift 2 ;;
    --)
      shift
      EXTRA+=("$@")
      break ;;
    *)
      EXTRA+=("$1"); shift ;;
  esac
done

if [[ ! -x "$SERVER" ]]; then
  echo "llama-server not found or not executable: $SERVER" >&2
  echo "This is a compiled binary. Python cannot find it for you." >&2
  echo "Build it (GTPS-Agent scripts/build_llama_server.sh) or set LLAMA_SERVER." >&2
  exit 1
fi
if [[ ! -f "$MODEL" ]]; then
  echo "model file not found: $MODEL" >&2
  exit 1
fi

echo "starting $SERVER" >&2
echo "  model $MODEL" >&2
echo "  port  $PORT   ctx $CTX   ngl $NGL   fa off" >&2

# -fa off last: auto/on means kq_soft_max never exists and RELIED refuses.
if [[ ${#EXTRA[@]} -gt 0 ]]; then
  exec "$SERVER" -m "$MODEL" -c "$CTX" -ngl "$NGL" --port "$PORT" "${EXTRA[@]}" -fa off
fi
exec "$SERVER" -m "$MODEL" -c "$CTX" -ngl "$NGL" --port "$PORT" -fa off
