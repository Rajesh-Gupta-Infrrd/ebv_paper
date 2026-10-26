#!/usr/bin/env bash
# Start the NuExtract-3 vLLM server (OpenAI-compatible) on a single A10.
# NuExtract 3 is Qwen3.5-VL-based (multimodal) — served directly with `vllm serve`.
set -euo pipefail

MODEL_ID="${NUEXTRACT_MODEL_ID:-numind/NuExtract3}"
HOST="${NUEXTRACT_HOST:-127.0.0.1}"
PORT="${NUEXTRACT_PORT:-30000}"
GPU_MEM_UTIL="${VLLM_GPU_MEM_UTIL:-0.90}"
MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-32768}"   # Qwen3.5-VL native 32k; real invoices need it
MAX_IMAGES="${VLLM_MAX_IMAGES_PER_PROMPT:-8}"   # RealKIE invoices are multi-page

echo "Serving ${MODEL_ID} on http://${HOST}:${PORT}  (gpu_mem_util=${GPU_MEM_UTIL}, max_len=${MAX_MODEL_LEN})"

# Notes:
#  - --trust-remote-code: NuExtract3 ships a custom (Qwen3.5-VL) processor.
#  - --limit-mm-per-prompt syntax varies by vLLM version; if this errors, try
#      --limit-mm-per-prompt image=${MAX_IMAGES}
#    or drop the flag (defaults usually allow a few images).
#  - For more VRAM headroom use the 4-bit repo: NUEXTRACT_MODEL_ID=numind/NuExtract3-W4A16
exec vllm serve "${MODEL_ID}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --trust-remote-code \
  --gpu-memory-utilization "${GPU_MEM_UTIL}" \
  --max-model-len "${MAX_MODEL_LEN}" \
  --limit-mm-per-prompt "{\"image\": ${MAX_IMAGES}}"
