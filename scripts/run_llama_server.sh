#!/usr/bin/env bash
# Start the llama.cpp server this runtime talks to.
#
# llama-server is a compiled binary at LLAMA_SERVER. It is not on PATH
# and it is not in this directory. Typing `llama-server` from here fails
# with "command not found". Claude Code's GTPS-Agent wrapper works for
# the same reason this one does: it calls the binary by full path.
# Working directory does not matter.
#
#   source env.sh
#   ./scripts/run_llama_server.sh
#   ./scripts/run_llama_server.sh -m /path/to/granite.gguf --port 8080 -c 4096
#
# Env (a matching CLI flag wins when both are set):
#   LLAMA_SERVER  binary — REQUIRED, no machine default
#   MODEL         .gguf path — REQUIRED unless -m is passed
#   PORT          default 8080   (run.py looks here)
#   CTX           default 8192   (drop to 4096 for the 8B on 6 GB)
#   NGL           default 99     (GPU layers). 0 = weights on CPU.
#                 A CUDA-built binary still parks compute buffers on the
#                 GPU unless --device none. This script adds that when NGL=0.
set -euo pipefail

if [[ -z "${LLAMA_SERVER:-}" ]]; then
  echo "LLAMA_SERVER is unset." >&2
  echo "Copy env.example.sh to env.sh, set the patched llama-server path, source env.sh." >&2
  exit 2
fi
SERVER="$LLAMA_SERVER"
PORT="${PORT:-8080}"
CTX="${CTX:-8192}"
NGL="${NGL:-99}"
# Beneath on a CUDA-filled card: a second, GGML_CUDA=OFF binary.
# NGL=0 on the hooked CUDA binary is not isolation (compute buffers
# still land on leftover VRAM, then OOM).
if [[ "$PORT" == "8081" && -n "${LLAMA_SERVER_BENEATH:-}" ]]; then
  SERVER="$LLAMA_SERVER_BENEATH"
fi

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

if [[ -z "${MODEL:-}" ]]; then
  echo "MODEL is unset." >&2
  echo "Set MODEL to a .gguf path in env.sh, or pass -m /path/to/model.gguf." >&2
  exit 2
fi
if [[ ! -x "$SERVER" ]]; then
  echo "llama-server not found or not executable: $SERVER" >&2
  echo "This is a compiled binary. Python cannot find it for you." >&2
  echo "Build it from DEPENDENCIES.md (pin b8461, apply patch, copy llama-hook/) and set LLAMA_SERVER." >&2
  exit 1
fi
if [[ ! -f "$MODEL" ]]; then
  echo "model file not found: $MODEL" >&2
  exit 1
fi

# NGL=0 is weights on CPU. A CUDA-linked llama-server still inits CUDA and
# tries ~0.5 GB compute buffers on leftover VRAM. --device none hides the
# GPU from this process (face on :8080 can keep the card).
DEVICE_NONE=()
have_dev=0
for a in "${EXTRA[@]+"${EXTRA[@]}"}"; do
  case "$a" in
    -dev|--device|--device=*) have_dev=1 ;;
  esac
done
if [[ "$NGL" == "0" && "$have_dev" -eq 0 ]]; then
  DEVICE_NONE=(--device none)
fi

echo "starting $SERVER" >&2
echo "  model $MODEL" >&2
echo "  port  $PORT   ctx $CTX   ngl $NGL   fa off" >&2
if [[ ${#DEVICE_NONE[@]} -gt 0 ]]; then
  echo "  device none  (NGL=0: do not park compute buffers on leftover VRAM)" >&2
fi

# -fa off last: auto/on means kq_soft_max never exists and RELIED refuses.
exec "$SERVER" -m "$MODEL" -c "$CTX" -ngl "$NGL" --port "$PORT" \
  "${DEVICE_NONE[@]}" "${EXTRA[@]+"${EXTRA[@]}"}" -fa off
