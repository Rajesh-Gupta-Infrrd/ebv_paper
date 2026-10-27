#!/usr/bin/env bash
# One-command orchestrator for the ROCKET GPU run (A10). Runs inside a 2-pane tmux session
# (same layout as extraction/setup_and_run.sh) so you see ALL logs live:
#   pane 0 (top)    = vLLM server log (NuExtract), then MinerU extract server (same as parse)
#   pane 1 (bottom) = extraction / MinerU progress
#
#   ./run_rocket.sh install     # create both venvs + deps (verbose; skips what's already installed)
#   ./run_rocket.sh smoke       # tiny end-to-end test (URLA x20 fields, CD x20 tables)
#   ./run_rocket.sh nuextract   # fields
#   ./run_rocket.sh mineru      # tables
#   ./run_rocket.sh all         # install (if needed) -> nuextract -> mineru
#   ./run_rocket.sh clean       # delete macOS ._* junk files from datasets/rocket
# Extra args pass through, e.g.:  ./run_rocket.sh nuextract --types URLA --limit 20
# Re-attach: tmux attach -t ebv_rocket     (detach: Ctrl+B then D)
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$HERE"
NEV="$HERE/nuextract-venv"; MEV="$HERE/mineru-venv"
PORT="${NUEXTRACT_PORT:-30000}"; MPORT="${MINERU_PORT:-30001}"; SESS="${TMUX_SESSION:-ebv_rocket}"
PY="$(command -v python3.12 || command -v python3)"
RDIR="${ROCKET_ROOT:-$HERE/../datasets/rocket}"
log() { echo -e "\033[1;36m[rocket]\033[0m $*"; }

clean() {   # tar from macOS leaves AppleDouble "._*.pdf" files that are not real PDFs
  find "$RDIR" -name '._*' -print -delete 2>/dev/null | wc -l | xargs -I{} echo "removed {} ._* files"
}

sysdeps() {
  command -v apt-get >/dev/null 2>&1 || return 0
  if ! command -v tmux >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
    log "apt: tmux curl python3-venv"
    sudo apt-get update -y && sudo apt-get install -y tmux curl python3-venv
  fi
}

install() {
  sysdeps
  log "nuextract-venv (vLLM + NuExtract client + PyMuPDF)"
  [ -x "$NEV/bin/python" ] || "$PY" -m venv "$NEV"
  if "$NEV/bin/python" -c "import vllm, requests, pymupdf, PIL" 2>/dev/null; then
    log "  already installed — skipping"
  else
    "$NEV/bin/pip" install -U pip wheel
    "$NEV/bin/pip" install --prefer-binary vllm requests pymupdf pillow
  fi

  log "mineru-venv (vLLM + mineru-vl-utils, same stack as DocAI parse)"
  [ -x "$MEV/bin/python" ] || "$PY" -m venv "$MEV"
  # EXACT parse stack (setup_parse_ubuntu.sh mineru-vllm-venv): vllm + mineru-vl-utils==1.0.5 + fastapi/uvicorn
  if "$MEV/bin/python" -c "import vllm, mineru_vl_utils, fastapi, uvicorn, pymupdf, PIL, requests" 2>/dev/null \
     && [ "$("$MEV/bin/pip" show mineru-vl-utils 2>/dev/null | awk '/^Version/{print $2}')" = "1.0.5" ]; then
    log "  already installed — skipping"
  else
    "$MEV/bin/pip" install -U pip wheel
    "$MEV/bin/pip" install --prefer-binary vllm 'mineru-vl-utils[transformers]==1.0.5' fastapi uvicorn requests pymupdf pillow \
      || "$MEV/bin/pip" install --only-binary vllm vllm 'mineru-vl-utils[transformers]==1.0.5' fastapi uvicorn requests pymupdf pillow
  fi
  "$NEV/bin/python" -c "import vllm, requests, pymupdf" && log "nuextract-venv OK"
  "$MEV/bin/python" -c "import vllm, mineru_vl_utils, fastapi" && log "mineru-venv OK"
  log "install done"
}

wait_health() {
  log "waiting for vLLM on :$PORT (first model load can take ~10 min)..."
  until curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1; do sleep 5; done
  log "vLLM ready."
}

# ---- inner steps (run inside tmux pane 1, foreground, fully verbose) ------------------
run_nuextract() {
  wait_health || return 1
  log "NuExtract extraction"
  "$NEV/bin/python" "$HERE/run_rocket_nuextract.py" "$@"
  local rc=$?
  log "stopping vLLM server (frees GPU)"
  tmux send-keys -t "$SESS:0.0" C-c 2>/dev/null
  sleep 8
  return $rc
}

start_mineru_server() {   # same launch as setup_parse_ubuntu.sh
  tmux send-keys -t "$SESS:0.0" "source '$MEV/bin/activate' && export MINERU_BACKEND=vllm-async-engine MINERU_MICRO_BATCH_MS=20 MINERU_MICRO_BATCH_MAX=8 CUDA_VISIBLE_DEVICES=0 && python '$HERE/mineru_extract_server.py' --host 127.0.0.1 --port $MPORT --preload 2>&1 | tee '$HERE/mineru_serve.log'" C-m 2>/dev/null
}

run_mineru() {
  start_mineru_server
  log "waiting for MinerU server on :$MPORT (model load)..."
  until curl -sf "http://127.0.0.1:$MPORT/health" >/dev/null 2>&1; do sleep 5; done
  log "MinerU server ready. Running client."
  MINERU_PORT=$MPORT "$MEV/bin/python" "$HERE/run_rocket_mineru.py" "$@"
  local rc=$?
  tmux send-keys -t "$SESS:0.0" C-c 2>/dev/null
  return $rc
}

inner() {
  local what="$1"; shift
  clean
  case "$what" in
    nuextract) run_nuextract "$@" ;;
    mineru)    run_mineru "$@" ;;
    smoke)     run_nuextract --types URLA --limit 20; run_mineru --types CD_tables --limit 20 ;;
    all)       run_nuextract "$@"; run_mineru ;;
  esac
  log "FINISHED ($what). Pane stays open; Ctrl+B then D to detach."
}

launch() {   # launch <what> [args...]
  local what="$1"; shift
  command -v tmux >/dev/null 2>&1 || { echo "tmux missing — run ./run_rocket.sh install"; exit 1; }
  [ -x "$NEV/bin/python" ] && [ -x "$MEV/bin/python" ] || { echo "run './run_rocket.sh install' first"; exit 1; }
  tmux kill-session -t "$SESS" 2>/dev/null || true
  local args=""; [ $# -gt 0 ] && args="$(printf '%q ' "$@")"
  tmux new-session -d -s "$SESS" -c "$HERE"
  tmux split-window -v -t "$SESS:0" -p 70 -c "$HERE"
  case "$what" in
    mineru) : ;;   # pane 0 gets the MinerU server from run_mineru
    *)      tmux send-keys -t "$SESS:0.0" "source '$NEV/bin/activate' && NUEXTRACT_PORT=$PORT bash '$HERE/../extraction/serve_nuextract.sh' 2>&1 | tee '$HERE/serve.log'" C-m ;;
  esac
  tmux send-keys -t "$SESS:0.1" "'$HERE/run_rocket.sh' _inner $what $args" C-m
  tmux select-pane -t "$SESS:0.1"
  log "tmux '$SESS': pane0=server/GPU, pane1=progress. Detach: Ctrl+B D; re-attach: tmux attach -t $SESS"
  tmux attach -t "$SESS"
}

cmd="${1:-all}"; shift 2>/dev/null || true
case "$cmd" in
  install)   install ;;
  clean)     clean ;;
  nuextract) launch nuextract "$@" ;;
  mineru)    launch mineru "$@" ;;
  smoke)     launch smoke ;;
  all)       install && launch all "$@" ;;
  _inner)    inner "$@" ;;
  *) echo "usage: $0 {install|smoke|nuextract|mineru|all|clean} [extra args]"; exit 1 ;;
esac
