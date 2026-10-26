#!/usr/bin/env bash
# Run the 6 VRDU ROI matrix runs (mirrors the FATURA methodology / names, vrdu-prefixed).
set -e
cd "$(dirname "$0")/.."
PY=/Users/rajeshgupta/Git_Clones/NTP/NTP/venv/bin/python

run() {  # geom corr calib name
  echo "=== $4 START $(date) ==="
  "$PY" scripts/run_matrix.py --dataset vrdu --geom "$1" --corr "$2" --calib "$3" --name "$4" 2>&1 \
    | grep -E "vrdu_|calib skip|->|Error|Traceback" | tail -8
  echo "=== $4 DONE $(date) ==="
}

run pred containment off vrdu_v1_pred_nocalib
run pred exact       on  vrdu_v2_pred_exact
run pred containment on  vrdu_v2_pred_contain
run gt   exact       on  vrdu_v3_gt_exact
run gt   containment on  vrdu_v3_gt_contain
run gt   exact       off vrdu_v4_gt_nocalib
echo "=== ALL VRDU ROI RUNS DONE $(date) ==="
