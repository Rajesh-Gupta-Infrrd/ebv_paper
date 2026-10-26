# experiments/ — the three legs + the indirect experiments

Pipeline: **Stage 1 extract** (produce predictions) → **Stage 2 label** (correct/wrong) →
**Stage 3 verify + score** (the EBV verifier + the indirect analysis).
Stage 1 (running the NuExtract-3 extractor over the benchmarks) is documented separately in
**`extraction/EXTRACTION_STAGE1.md`**. Everything below is Stages 2–3: each leg **re-scores stored
extractor outputs** (no re-extraction).

## Directory map
Each system dir has shared `scripts/` plus **one sub-dir per benchmark** (so every result/log is unambiguous).

| Dir | Leg | Benchmark sub-dirs | Findings doc |
|---|---|---|---|
| `structured_ntp/` | **Structured (ROI)** | `fatura/`, `vrdu/` (+ shared `scripts/ inputs/ splits/`) | `fatura/paper/STRUCTURED_EXPERIMENT.md`, `vrdu/paper/STRUCTURED_VRDU.md`, `fatura/paper/competitor_comparison.md` |
| `unstructured_ntp/` | **Unstructured (Signal)** | `realkie_fcc/`, `realkie_s1/`, `realkie_charities/`, `realkie_nda/` (+ shared `scripts/`) | `realkie_fcc/paper/UNSTRUCTURED_realkie_fcc.md`, each `realkie_*/paper/UNSTRUCTURED_<ds>.md`; `ROBUSTNESS_EXPERIMENTS.md` combines domains |
| `tables/` | **Tables** — RD + ParseBench | `parsebench/`, `_dropped_omnidoc/` (RD eval is in the **DocAI** repo) | `paper/TABLES_EXPERIMENT.md` |
| `indirect/` | **Indirect** — frontier, map, complementarity, ablation, oracle, sufficiency, lineage, shift | `scripts/` + `analysis/*.json` | `INDIRECT_EXPERIMENTS.md` |
| `results/` | stored extraction outputs + ground truth per dataset | — | the inputs the legs re-score (git-ignored data) |
| `_archive/` | superseded material (structured v1 tar) | — | kept locally, git-ignored |

## The FINALIZED combination per benchmark (reconcile targets)
Every runner prints a reconciliation line proving its AUROC matches these:

| Benchmark | Finalized config | AUROC |
|---|---|---|
| FATURA | GT-ROI · exact · calib-ON · **A-handled (keepB)**; score = `wv_score` | 0.994 |
| VRDU | v3 · GT-ROI · exact; score = `wv_score` | 0.896 / 0.927 (excl. signature) |
| Signal (FCC/S1/Charities) | `bundle_clean` · binary · **scalar** fields; score = **`proba`**; correctness = normalized containment | 0.897 / 0.960 / 0.713 |
| RD-TableBench | Table-Trust `trust`; **ACCEPT iff trust ≥ 85**; GT = **vision**-adjudicated | bad-catch 0.899 |
| ParseBench | Table-Trust `trust` ≥ 85; GT = **vision** | 0.912 |

## Indirect — where to start
`indirect/scripts/lib_frontier.py` is the shared library; each `run_*.py` is self-contained and
**reconciles first**. See `indirect/INDIRECT_EXPERIMENTS.md` §7 for the full file list and the
output each produces. The headline (detectability frontier) and status are in the top-level `README.md`.
