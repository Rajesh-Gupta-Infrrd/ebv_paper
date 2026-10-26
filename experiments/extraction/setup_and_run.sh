#!/usr/bin/env bash
# =============================================================================
# EBV extraction — one-shot setup + run on a remote GPU box (A10 / Lambda).
# Mirrors the DocAI "parse" pattern: install | start | all subcommands, a
# dedicated --prefer-binary vLLM venv, headless dataset download, a tmux session
# with a curl health-wait loop, then the extraction orchestrator.
#
#   ./setup_and_run.sh install        # system deps + venv + datasets
#   ./setup_and_run.sh start          # tmux: serve NuExtract + run extraction
#   ./setup_and_run.sh all            # install then start
#   ./setup_and_run.sh serve          # just run the vLLM server (foreground)
#
# Pick the dataset for `start`/`all` with:
#   DATASET=fatura | realkie_fcc | realkie_charities | realkie_nda | realkie_s1 | vrdu
# (`start` downloads only the chosen dataset, so you never pull all 50 GB at once.)
# =============================================================================
set -euo pipefail

EXP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAPER_DIR="$(dirname "$(dirname "$EXP_DIR")")"
VENV="${VENV:-$EXP_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
TMUX_SESSION="${TMUX_SESSION:-ebv_extract}"
PORT="${NUEXTRACT_PORT:-30000}"
DATASET="${DATASET:-fatura}"
RUN_ARGS="${RUN_ARGS:---resume --max-workers 8}"

export FATURA_ROOT="${FATURA_ROOT:-$PAPER_DIR/experiments/datasets/fatura}"
export REALKIE_FCC_ROOT="${REALKIE_FCC_ROOT:-$PAPER_DIR/experiments/datasets/realkie_fcc_invoices}"
export REALKIE_CHARITIES_ROOT="${REALKIE_CHARITIES_ROOT:-$PAPER_DIR/experiments/datasets/realkie_charities}"
export REALKIE_NDA_ROOT="${REALKIE_NDA_ROOT:-$PAPER_DIR/experiments/datasets/realkie_nda}"
export REALKIE_S1_ROOT="${REALKIE_S1_ROOT:-$PAPER_DIR/experiments/datasets/realkie_s1}"
export VRDU_ROOT="${VRDU_ROOT:-$PAPER_DIR/experiments/datasets/vrdu/registration-form}"

log() { echo -e "\033[1;36m[ebv]\033[0m $*"; }
die() { echo -e "\033[1;31m[ebv] ERROR:\033[0m $*" >&2; exit 1; }

# ----------------------------------------------------------------------------- #
install_system_deps() {
  log "Installing system deps…"
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y python3.12 python3.12-dev python3.12-venv git curl wget aria2 tmux unzip p7zip-full poppler-utils build-essential
    PYTHON_BIN="python3.12"
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y git tmux gcc gcc-c++ make wget aria2 unzip p7zip poppler-utils python3.12 python3.12-devel || true
    PYTHON_BIN="python3.12"
  else
    die "no apt-get or dnf found; install python3.12-dev, tmux, wget, unzip manually"
  fi
}

install_python() {
  log "Creating venv $VENV (prefer-binary vLLM)…"
  [[ -d "$VENV" ]] || "$PYTHON_BIN" -m venv "$VENV"
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  pip install -U pip
  pip install --prefer-binary -r "$EXP_DIR/requirements.txt" \
    || pip install --only-binary vllm --prefer-binary -r "$EXP_DIR/requirements.txt"
  deactivate
}

# Download + unzip a dataset only if its root is missing. Robust to the zip
# having a top-level folder: we locate the inner dir and symlink it to the root.
_fetch_unzip() {
  local url="$1" zip="$2" root="$3" marker="$4"
  if [[ -d "$root" && -e "$root/$marker" ]]; then
    log "  $root already present — skipping download"; return 0
  fi
  local tmp; tmp="$(mktemp -d)"
  log "  downloading $zip …"
  # Zenodo throttles per-connection; aria2c with many connections is ~10-50x faster.
  if command -v aria2c >/dev/null 2>&1; then
    aria2c -x16 -s16 --max-tries=0 --retry-wait=5 --console-log-level=warn \
           -d "$tmp" -o "$zip" "$url"
  else
    wget -c "$url" -O "$tmp/$zip"
  fi
  log "  unzipping …"
  unzip -q "$tmp/$zip" -d "$tmp/unz"
  # find the dir that actually contains the marker (images/ or Annotations/)
  local inner; inner="$(dirname "$(find "$tmp/unz" -maxdepth 3 -name "$marker" -print -quit)")"
  [[ -n "$inner" && -e "$inner/$marker" ]] || die "could not locate '$marker' inside $zip"
  mkdir -p "$(dirname "$root")"
  rm -rf "$root"; mv "$inner" "$root"
  log "  → $root"
}

fetch_fatura() {
  _fetch_unzip "https://zenodo.org/records/10371464/files/FATURA2.zip?download=1" \
    "FATURA2.zip" "$FATURA_ROOT" "Annotations"
}
fetch_fcc() {
  _fetch_unzip "https://zenodo.org/records/13327077/files/fcc_invoices.zip?download=1" \
    "fcc_invoices.zip" "$REALKIE_FCC_ROOT" "images"
}
fetch_charities() {   # RealKIE Charities — 5.6 GB, same Zenodo record as FCC
  _fetch_unzip "https://zenodo.org/records/13327077/files/charities.zip?download=1" \
    "charities.zip" "$REALKIE_CHARITIES_ROOT" "images"
}
fetch_nda() {         # RealKIE NDA — 888 MB
  _fetch_unzip "https://zenodo.org/records/13327077/files/nda.zip?download=1" \
    "nda.zip" "$REALKIE_NDA_ROOT" "images"
}
fetch_s1() {          # RealKIE S-1 — 3.9 GB (SEC IPO filings, pre-split into pages)
  _fetch_unzip "https://zenodo.org/records/13327077/files/s1_pages.zip?download=1" \
    "s1_pages.zip" "$REALKIE_S1_ROOT" "images"
}

# VRDU Registration-Forms (FARA) — git repo (PDFs + dataset.jsonl.gz, NOT LFS).
# Sparse-checkout only registration-form/, then gunzip + render page PNGs.
fetch_vrdu() {
  local root="$VRDU_ROOT" clone_dir
  clone_dir="$(dirname "$root")"        # …/vrdu  (VRDU_ROOT = …/vrdu/registration-form)
  if [[ -f "$root/main/dataset.jsonl" || -f "$root/main/dataset.jsonl.gz" ]]; then
    log "  VRDU already checked out — skipping clone"
  else
    log "  sparse-cloning VRDU registration-form (public-domain FARA PDFs)…"
    rm -rf "$clone_dir"
    git clone --depth 1 --filter=blob:none --sparse \
      https://github.com/google-research-datasets/vrdu.git "$clone_dir"
    git -C "$clone_dir" sparse-checkout set registration-form
  fi
  log "  preparing VRDU (gunzip dataset.jsonl + render page images with pdftoppm)…"
  ( source "$VENV/bin/activate" && python "$EXP_DIR/prep_vrdu.py" )
}

# Explicit pre-fetch of THIS round's new datasets (only when you ask for it via the
# `download` subcommand). `install` no longer downloads anything, and `start` pulls
# just the one dataset you name — so fresh boxes never re-pull FATURA/FCC.
download_datasets() { log "Fetching this round's datasets…"; fetch_vrdu; fetch_charities; fetch_nda; }

# Ensure ONLY the dataset we're about to run is present (first-time safety for `start`).
ensure_dataset() {
  case "$1" in
    fatura)            fetch_fatura ;;
    realkie_fcc)       fetch_fcc ;;
    realkie_charities) fetch_charities ;;
    realkie_nda)       fetch_nda ;;
    realkie_s1)        fetch_s1 ;;
    vrdu)              fetch_vrdu ;;
    *) die "unknown DATASET '$1' (use fatura|realkie_fcc|realkie_charities|realkie_nda|realkie_s1|vrdu)" ;;
  esac
}

# ----------------------------------------------------------------------------- #
wait_health() {
  log "Waiting for vLLM at http://127.0.0.1:${PORT}/v1/models …"
  until curl -sf "http://127.0.0.1:${PORT}/v1/models" >/dev/null 2>&1; do sleep 5; done
  log "server is up."
}

start_tmux() {
  command -v tmux >/dev/null 2>&1 || die "tmux not installed (run: $0 install)"
  if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    log "tmux session '$TMUX_SESSION' already exists — attaching (extraction runs with --resume, so it just continues)."
    exec tmux attach -t "$TMUX_SESSION"
  fi
  ensure_dataset "$DATASET"   # first-time safety: download the chosen dataset if missing
  log "Launching tmux session '$TMUX_SESSION' (pane 0 = server, pane 1 = extraction on '$DATASET')"
  tmux new-session -d -s "$TMUX_SESSION" -c "$EXP_DIR"
  tmux split-window -v -t "$TMUX_SESSION:0" -p 70 -c "$EXP_DIR"

  # pane 0 — server
  tmux send-keys -t "$TMUX_SESSION:0.0" \
    "source '$VENV/bin/activate' && NUEXTRACT_PORT=$PORT bash serve_nuextract.sh" C-m

  # pane 1 — wait for health, then run extraction
  tmux send-keys -t "$TMUX_SESSION:0.1" \
    "source '$VENV/bin/activate' && \
     echo 'waiting for server…' && until curl -sf http://127.0.0.1:${PORT}/v1/models >/dev/null 2>&1; do sleep 5; done && \
     echo 'server up — starting extraction' && \
     python run_extraction.py --dataset $DATASET $RUN_ARGS" C-m

  tmux select-pane -t "$TMUX_SESSION:0.1"
  log "Attach with:  tmux attach -t $TMUX_SESSION   (detach: Ctrl+B then D)"
  tmux attach -t "$TMUX_SESSION"
}

# ----------------------------------------------------------------------------- #
cmd="${1:-all}"
case "$cmd" in
  install)  install_system_deps; install_python ;;                      # deps + venv ONLY (no data)
  start)    start_tmux ;;                                               # downloads ONLY $DATASET
  all)      install_system_deps; install_python; start_tmux ;;         # install + run the chosen DATASET
  download) download_datasets ;;                                        # optional: pre-fetch vrdu+charities+nda
  serve)    source "$VENV/bin/activate"; NUEXTRACT_PORT=$PORT bash "$EXP_DIR/serve_nuextract.sh" ;;
  *)        die "usage: $0 {install|start|all|download|serve}  (DATASET=fatura|realkie_fcc|realkie_charities|realkie_nda|realkie_s1|vrdu)" ;;
esac
