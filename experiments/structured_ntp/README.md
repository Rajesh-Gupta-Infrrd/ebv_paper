# structured_ntp — ROI verifier (structured leg): FATURA + VRDU

Runs NTP's **full** production ROI pipeline offline (all layers ON: weight+threshold
calibration, keyword-context boost, empty-field handling, per-field thresholds) and scores
its outputs. Run the scripts with `/Users/rajeshgupta/Git_Clones/NTP/NTP/venv/bin/python`
(imports `compute_roi`).

## Layout (per-benchmark)
```
structured_ntp/
├── scripts/          shared scripts for both benchmarks (run_v2, run_matrix, clean_gt,
│                     doc_structured[_vrdu], compute_[vrdu_]auroc_coverage, recompute_fatura_clean,
│                     prep_vrdu_roi, diagnose_*, analyze_*)
├── inputs/           OCR token files reused by both (fatura_ocr, vrdu_ocr)  — git-ignored (large)
├── splits/           per-template 70/30 splits (fatura_split.json, vrdu_split.json)
├── fatura/           synthetic invoices
│   ├── matrix/       ROI-source × calibration × correctness runs (v1_pred_nocalib … v4_gt_nocalib)
│   ├── task1_predroi_containment/  task3a_predroi_exact/  task3b_gt_endtoend_exact/   (the 3 ROI tasks)
│   ├── gt_clean/     cleaned GT + cleaning_quality.json
│   ├── ablation/     Cp-constant / GT-constant ablations
│   ├── logs/         run logs for the above
│   └── paper/        STRUCTURED_EXPERIMENT.md (start here), competitor_comparison.md, matrix_table.md, fatura_clean_auroc_coverage.json
└── vrdu/             real templatic FARA forms (same pipeline)
    ├── matrix/       vrdu_v1_pred_nocalib … vrdu_v3_gt_exact (+ smoke_vrdu)
    ├── gt_clean/  logs/
    └── paper/        STRUCTURED_VRDU.md, structured_vrdu_metrics.json
```
Each `matrix/` or task dir holds `decisions.jsonl` (+ `roi_models/`, `datasets/`, `analysis/`).

## Finalized configs (reconcile targets)
- **FATURA:** `fatura/task3b_gt_endtoend_exact` (GT-ROI · exact · calib-ON, A-handled) → AUROC **0.994**.
- **VRDU:** `vrdu/matrix/vrdu_v3_gt_exact` (GT-ROI · exact) → AUROC **0.896** (all) / **0.927** (excl. signature).

## Reproduce
```
PY=/Users/rajeshgupta/Git_Clones/NTP/NTP/venv/bin/python
# FATURA
$PY scripts/clean_gt.py
for t in task1 task3a task3b; do $PY scripts/run_v2.py --task $t --templates all; $PY scripts/analyze_v2.py --task $t; done
# VRDU (reuses the same pipeline via --dataset vrdu)
$PY scripts/prep_vrdu_roi.py
$PY scripts/run_matrix.py --dataset vrdu --geom gt --corr exact --calib on --name vrdu_v3_gt_exact
```

> The earlier v1 run (defaults, no calibration, containment) is archived at
> `experiments/_archive/structured_ntp_v1.tar.gz` (its `inputs/` + `splits/` were merged here).
