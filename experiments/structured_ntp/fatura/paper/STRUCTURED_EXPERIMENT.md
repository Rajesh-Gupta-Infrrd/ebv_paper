# Structured (ROI) NTP experiment — full documentation

Verifies document-extraction field values with NTP's spatial ROI verifier (no extra LLM/VLM call)
on **FATURA** (50 templates, 10,000 synthetic invoices). Extractor = NuExtract-3. All runs drive
NTP's real pipeline **offline** (no Mongo) via `/Users/rajeshgupta/Git_Clones/NTP/NTP/venv/bin/python`.

## Pipeline
`compute_roi_for_doc_type` (ROI geometry + per-field thresholds + context keywords) →
`calibrate_from_evaluation_dataframes` (grid-searched per-field weights + score threshold) →
`evaluate_doc_type` (spatial score + keyword-context boost + empty-field handling → accept/route).
Per-template 70/30 split (seed 42): 7,000 train / 3,000 test docs. Templates scored independently
(verified: cleaning absent fields before vs after the pipeline gives 0 decision differences).

## The two axes
- **ROI geometry source**: `pred` = learned from where the extractor's *correct* predictions land;
  `GT` = learned from the (cleaned) ground-truth values (production's way).
- **Weight calibration**: `ON` = grid-searched per-field weights+threshold; `OFF` = NTP defaults
  (overlap/center/iou = .50/.30/.20, score_threshold 0.70).
- **Correctness (a LABEL, not a pipeline toggle)**: `exact` = NTP field-aware matcher on cleaned GT;
  `containment` = normalized-alnum substring match (lenient; robust to FATURA's label-bundled GT).
- **Population**: `present` = fields that exist in the doc's GT (the honest spatial task);
  `full` = present + hallucinations on absent fields (trivially routed → inflates catch).

## Versions (enabled / disabled)
All four use the full pipeline: per-field thresholds, keyword boost, and empty-field handling are **ENABLED** in every version. They differ only as:
| version | ROI geometry | weight calibration | per-field thresholds | keyword boost | empty handling |
|---|---|---|---|---|---|
| **v1** | correct predictions | **OFF (defaults)** | on | on | on |
| **v2** | correct predictions | **ON (grid search)** | on | on | on |
| **v3** | **GT (production)** | **ON (grid search)** | on | on | on |
| **v4** | **GT (production)** | **OFF (defaults)** | on | on | on |
(The earlier `../structured_ntp/` run was a direct-primitive prototype: defaults + pred-ROI + containment, with keyword/empty **disabled** — superseded by v1 here, which reproduces its catch.)

## RESULTS — present-field population (the honest spatial-detectability numbers)
| ver | config | correctness | n | err-rate | error-catch ↑ | false-alarm ↓ | route-prec ↑ | accuracy ↑ | AURC ↓ |
|---|---|---|---|---|---|---|---|---|---|
| v1 | pred-ROI, calib OFF | exact | 28468 | 0.102 | 0.5348 | 0.0503 | 0.5470 | 0.9074 | 0.0115 |
| v1 | pred-ROI, calib OFF | containment | 29199 | 0.056 | 0.9994 | 0.0497 | 0.5425 | 0.9530 | 0.0002 |
| v2 | pred-ROI, calib ON | exact | 28468 | 0.102 | 0.6119 | 0.0446 | 0.6092 | 0.9204 | 0.0098 |
| v2 | pred-ROI, calib ON | containment | 29199 | 0.056 | 0.9994 | 0.0388 | 0.6031 | 0.9633 | 0.0002 |
| v3 | GT-ROI, calib ON (prod) | exact | 28468 | 0.102 | 0.6143 | 0.0870 | 0.4451 | 0.8825 | 0.0093 |
| v3 | GT-ROI, calib ON (prod) | containment | 29199 | 0.056 | 1.0000 | 0.0963 | 0.3801 | 0.9091 | 0.0000 |
| v4 | GT-ROI, calib OFF | exact | 28468 | 0.102 | 0.5954 | 0.0915 | 0.4250 | 0.8766 | 0.0091 |
| v4 | GT-ROI, calib OFF | containment | 29199 | 0.056 | 1.0000 | 0.1058 | 0.3580 | 0.9001 | 0.0001 |

## RESULTS — full population (includes absent-field hallucinations; catch is inflated)
| ver | config | correctness | n | err-rate | error-catch ↑ | false-alarm ↓ | route-prec ↑ | accuracy ↑ | AURC ↓ |
|---|---|---|---|---|---|---|---|---|---|
| v1 | pred-ROI, calib OFF | exact | 36370 | 0.297 | 0.8220 | 0.0503 | 0.8735 | 0.9117 | 0.0112 |
| v1 | pred-ROI, calib OFF | containment | 36370 | 0.242 | 0.9999 | 0.0497 | 0.8652 | 0.9623 | 0.0001 |
| v2 | pred-ROI, calib ON | exact | 36370 | 0.297 | 0.8743 | 0.0446 | 0.8923 | 0.9313 | 0.0103 |
| v2 | pred-ROI, calib ON | containment | 36370 | 0.242 | 0.9999 | 0.0388 | 0.8916 | 0.9706 | 0.0001 |
| v3 | GT-ROI, calib ON (prod) | exact | 36370 | 0.297 | 0.8750 | 0.0870 | 0.8096 | 0.9017 | 0.0097 |
| v3 | GT-ROI, calib ON (prod) | containment | 36370 | 0.242 | 1.0000 | 0.0963 | 0.7683 | 0.9270 | 0.0000 |
| v4 | GT-ROI, calib OFF | exact | 36370 | 0.297 | 0.8678 | 0.0915 | 0.8004 | 0.8964 | 0.0086 |
| v4 | GT-ROI, calib OFF | containment | 36370 | 0.242 | 1.0000 | 0.1058 | 0.7509 | 0.9198 | 0.0000 |
*(↑ higher better, ↓ lower better. Correctness is a label on identical accept/route decisions.)*

## Key findings
1. **Containment → exact drives the catch gap, but it is MOSTLY a labeling artefact, not the true frontier.** The strict-exact "errors" decompose into **A** value-right-but-exact-wrong (20.8%), **B** GT-empty/sparsity (66.4%), **C** genuine in-place value error (12.8%) — see `competitor_comparison.md`. The verifier correctly *accepts* the type-A items (they are spatially correct), which is what depresses exact-catch vs containment. The **real detectability frontier** — errors spatial truly cannot catch (right location, wrong value) — is only **type C: 12.8% of errors / 3.8% of predictions**, far smaller than the raw containment→exact gap suggests. Those need the text/content channel.
2. **Weight calibration gives a modest lift** under exact (pred-ROI 0.535→0.612; GT-ROI 0.595→0.614) and lowers false-alarm. It helps approach the ceiling; it does not raise the ceiling.
3. **Prediction-ROI ≥ GT-ROI** for verifying this extractor: v2 vs v3 (exact) catch ties (~0.61) but pred-ROI has ~half the false-alarm (0.045 vs 0.087) and higher accuracy (0.920 vs 0.883). Learning the region from the extractor's own correct outputs aligns it to that extractor. (GT-ROI remains the more general/principled choice; v3 is the production headline.)
4. **Absent-field hallucinations are a separate, trivially-caught error type** (≈100% routed; no ROI exists). They inflate full-population catch to ~0.81 and should be reported separately, not as the spatial result.
5. **Finalized paper config = v3 (GT-ROI, calib ON, exact).** v2 (pred-ROI) scores marginally better on *this* extractor, but we report GT-ROI + exact: a reviewer would rightly ask "why pred-ROI, not GT?" and "why lenient containment?", and GT-ROI is the general/principled choice. It also does not generalize (on VRDU, pred-ROI+calib collapses, AUROC 0.398). So v2 stays an internal observation, not the headline.
6. **Fair AUROC vs the Jin et al. competitor = parity at zero extra call.** After handling the type-A labeling artefact (A→correct; B+C kept as errors), v3 GT-ROI reaches **AUROC 0.994, cov@≤5% 69.8%** — on par with Jin's fused multi-call system (0.990–0.997) with **no extra LLM/VLM call**. Strict-exact (raw GT) is 0.865; containment-tolerant A-handling is a generous bound, so true capability is in [0.865, 0.994]. Full detail + caveats in `competitor_comparison.md`. **Paper reporting (2026-10-28):** the paper's headline FATURA AUROC is the **end-to-end 0.95** — AUROC over *all* present fields, with fields the verifier cannot score counted as lowest-trust. The **0.994** here is the scored-field (localized) AUROC and is no longer quoted as the headline (avoids a localization-conditional number).
7. **Document-level cost**: with ~10% field-level routing (present, exact) and ~98% of docs holding ≥1 exact-error, "accept iff all units accept" routes a large majority of documents — the honest usability cost on this clean/rigid dataset.

## Directory map (under experiments/)
```
structured_ntp/                 # v0 prototype: direct primitives, defaults, containment (superseded)
  inputs/fatura_ocr/            #   10k OCR token files (0-1000 space) — reused by v2
  splits/fatura_split.json      #   per-template 70/30 split (seed 42) — reused by v2
structured_ntp_v2/              # THIS experiment
  gt_clean/                     # Task-2 cleaned GT + cleaning_quality.json
  task1_predroi_containment/    # v2 containment  (decisions.jsonl, roi_models/, datasets/, analysis/, paper/)
  task3a_predroi_exact/         # v2 exact
  task3b_gt_endtoend_exact/     # v3 exact (production)
  matrix/v1_pred_nocalib/       # v1 (both labels)
  matrix/v3cont_gt_calib_contain/   # v3 containment
  matrix/v4_gt_nocalib/         # v4 (both labels)
  matrix/v2clean_exact|contain/ # validation: cleaned-input reruns (0 diffs vs filtered)
  paper/matrix_table.md         # the 8-row present table
  paper/comparison.md           # earlier cross-task summary
  paper/STRUCTURED_EXPERIMENT.md# THIS document
  scripts/                      # clean_gt.py, run_matrix.py, analyze_matrix.py, compare_clean.py, doc_structured.py
```

## Reproduce
```
PY=/Users/rajeshgupta/Git_Clones/NTP/NTP/venv/bin/python
$PY scripts/clean_gt.py
# v2 (both labels): calibration on
$PY scripts/run_matrix.py --geom pred --corr exact       --calib on  --name task3a_predroi_exact   # (or reuse task dirs)
$PY scripts/run_matrix.py --geom pred --corr containment --calib on  --name task1_predroi_containment
# v1 / v3-containment / v4
$PY scripts/run_matrix.py --geom pred --corr containment --calib off --name v1_pred_nocalib
$PY scripts/run_matrix.py --geom gt   --corr containment --calib on  --name v3cont_gt_calib_contain
$PY scripts/run_matrix.py --geom gt   --corr exact       --calib off --name v4_gt_nocalib
$PY scripts/doc_structured.py   # regenerate this doc + tables
# validation (optional): identical present-field results from cleaned input
$PY scripts/run_matrix.py --geom pred --corr exact --calib on --present-only --name v2clean_exact
$PY scripts/compare_clean.py
```

## Data provenance
Predictions + GT: `experiments/results/fatura_results/` (extraction_results_fatura.json, ground_truth_fatura.json — 10k docs, NuExtract-3). OCR: FATURA `layoutlm_HF_format` → `structured_ntp/inputs/fatura_ocr/`.
Validation: `compare_clean.py` → 0/31,378 (exact) and 0/29,199 (containment) decision differences between cleaned-input reruns and present-field-filtered originals.
