# EBV — Evidence-Based Verification of Document AI outputs

Research workspace for the EBV paper. **One idea:** verify a document-extraction output
(a structured field, an unstructured field, or a table) using only **in-document evidence,
with no extra LLM/VLM call**, and **measure the detectability frontier** — which extraction
errors leave a detectable trace and which don't.

> New here? Read this file, then `docs/ebv_paper.md` (the draft) and
> `docs/evidence_based_document_ai_verification_research_spec_v3.md` (the locked plan).
> Each experiment leg has its own findings doc (see the table below).

---

## 1. What's in this repo
```
ebv_paper/
├── README.md              ← you are here (map + headline results + how to reproduce)
├── docs/                  the paper + spec + related work + dataset exploration (+ _archive/ = superseded versions)
├── experiments/           the three legs + the indirect experiments (code, results, findings)
├── data/                  README only — raw datasets are NOT committed (see data/README.md)
└── .gitignore             excludes raw data, venvs, caches, logs, large binaries
```
Raw datasets, virtualenvs, caches and logs are git-ignored (see `.gitignore`); everything
needed to *understand and re-score* the work is committed.

## 2. The system — one unified verifier, three modes (a router picks the mode)
| Mode | What it verifies | Verifier | Public benchmarks (finalized) |
|---|---|---|---|
| **Structured** (ROI) | templatic fields (fixed positions) | spatial-grounding ROI signals | FATURA, VRDU |
| **Unstructured** (Signal) | free-text fields | text signals → small classifier | RealKIE: FCC, S1, Charities |
| **Tables** (Table-Trust) | extracted tables | structural signals + independent OCR witness | RD-TableBench, ParseBench |

## 3. Headline results (direct experiments — all reconciled)
| Leg | Benchmark | Result |
|---|---|---|
| Structured | FATURA (handled-A) | AUROC **0.994** |
| Structured | VRDU | AUROC **0.896** (all) / **0.927** (excl. signature) |
| Unstructured | FCC / S1 / Charities | AUROC **0.897 / 0.960 / 0.713** |
| Tables | RD-TableBench | bad-catch **0.899** at trust≥85 (precision-first) |
| Tables | ParseBench | AUROC **0.912** (visual adjudication; TEDS shown invalid as a label) |

Competitors: structured vs Jin et al. (P/L/V); unstructured vs ConfBench. Tables have **no**
same-benchmark competitor (architectural comparison). OmniDocBench was evaluated and **dropped**.

## 4. Indirect experiments — the detectability frontier (the novelty, H5)
At the deployed operating point the verifier catches most errors; the residual (the frontier)
is **evidence-dependent and small**: ~0% (FATURA, ParseBench), 0–8% on fields (S1 0%, FCC/VRDU
1–6%, Charities 8%), **10.6%** on RD tables. Adjudication: **0/31** confidently-wrong cases are
*fundamentally* undetectable — the information is in the document — so it's a **cost/coverage
frontier** (catchable with more evidence), flagged as INSUFFICIENT rather than falsely verified.
Full writeup + the complete experiment matrix (E2 ablation, E3b atlas, E4c oracle decomposition,
E5 sufficiency, E4b lineage, E6 shift, placebo, CIs): **`experiments/indirect/INDIRECT_EXPERIMENTS.md`**.

## 5. Where the findings live (one doc per leg)
| Leg | Findings doc |
|---|---|
| Structured | `experiments/structured_ntp/fatura/paper/STRUCTURED_EXPERIMENT.md` (+ `structured_ntp/vrdu/paper/STRUCTURED_VRDU.md`, `fatura/paper/competitor_comparison.md`) |
| Unstructured | `experiments/unstructured_ntp/realkie_fcc/paper/UNSTRUCTURED_realkie_fcc.md` (+ each `realkie_*/paper/UNSTRUCTURED_<ds>.md`, `experiments/ROBUSTNESS_EXPERIMENTS.md`) |
| Tables | `experiments/tables/paper/TABLES_EXPERIMENT.md` |
| Indirect | `experiments/indirect/INDIRECT_EXPERIMENTS.md` |

## 6. Reproducing
- **No re-extraction needed** — every experiment re-scores stored outputs.
- **Interpreters (separate venvs, git-ignored — recreate from the deps below):**
  - Unstructured/indirect: `experiments/unstructured_ntp/.venv` — Python 3.14; `scikit-learn 1.9.1, pandas 3.0.6, numpy 2.5.4, joblib 1.6.0`.
  - Structured/VRDU: the NTP repo venv at `/Users/<you>/Git_Clones/NTP/NTP/venv` (imports `compute_roi`).
  - Tables scorer: the **DocAI** repo venv (`.venv` with docTR, PIL, TEDS deps).
- **Cross-repo dependency (important):** the **tables leg's scorer and RD/ParseBench eval live in
  the separate `DocAI` repo**, not here:
  - scorer: `DocAI/scripts/extract/table_extractor/scoring.py`
  - RD eval + review data: `DocAI/eval/table_extraction/rdbench/`
  - ParseBench outputs: `DocAI/eval/table_extraction/parsebench/`
- Raw datasets: see `data/README.md` (not committed).

## 7. Status
- **Direct experiments:** done (all three legs + competitor comparisons).
- **Indirect experiments:** done — frontier, detectability map (all modes), complementarity,
  ablation, oracle decomposition, sufficiency (tested → dropped), lineage, shift, placebo, CIs.
- **Only pending:** the **LLM-judge / equal-cost baseline (E-cost / H1)** — needs a paid model
  call per item, so it's a budget decision (not a cheap re-run). `E3a` (controlled corruption)
  and a field-side independent witness (`P1`) were intentionally **not** done (optional / would
  add a model call and undercut the zero-extra-call claim).

## 8. Standing conventions
Simple, genuine language; **publish numbers, not data**; claim only from stored results; keep
the production `dociq` repo untouched; one unified system (router → modes) reported per failure
family and per leg.
