#!/usr/bin/env bash
# One-time A10 setup: two venvs (NuExtract via vLLM, MinerU). They each hold the GPU,
# so run them SEQUENTIALLY (NuExtract fully, then MinerU). Run from this rocket_gpu/ dir.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$HERE"

echo "== system deps =="
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y && sudo apt-get install -y python3.12 python3.12-venv git || true
fi
PY="$(command -v python3.12 || command -v python3)"

echo "== nuextract-venv (vLLM server + NuExtract client + PyMuPDF) =="
"$PY" -m venv nuextract-venv
./nuextract-venv/bin/pip install -U pip wheel
./nuextract-venv/bin/pip install vllm requests pymupdf pillow

echo "== mineru-venv (MinerU 2.x + vLLM backend) =="
"$PY" -m venv mineru-venv
./mineru-venv/bin/pip install -U pip wheel
./mineru-venv/bin/pip install -U "mineru[core]" vllm

echo
echo "DONE. Next (see README_ROCKET_GPU.md):"
echo "  1) NuExtract:  source nuextract-venv/bin/activate; bash ../extraction/serve_nuextract.sh &"
echo "                 python run_rocket_nuextract.py ; then stop the vLLM server"
echo "  2) MinerU:     source mineru-venv/bin/activate;  python run_rocket_mineru.py"
