# Response to PENDING_C_PORT (author/colleague items), 2026-10-29

Context: most of `PENDING_C_PORT_2026-10-28.md` is you porting our already-committed
`ab549ac` fixes into the LaTeX — nothing needed from us there. This file answers only
the threads you tagged **author / colleague / "must compute" / "author to recheck."**
All numbers below were computed from committed repo data (paths given), not estimated.

---

## 12g — Is the OCR witness independent? **Yes. Claim holds; one phrasing to soften.**

**What you asked / why:** archived notes suggested the witness might reuse the pipeline's
own docTR tokens and only re-run docTR on the crop behind a flag; if the pipeline OCR was
docTR, "separate from the engine that produced the pipeline's tokens" would be false.

**What I did:** traced `score_table_trust` in
`/Users/rajeshgupta/Projects/DocAI/scripts/extract/table_extractor/scoring.py` and the
three table-scoring runs in `experiments/rocket_gpu/`.

**Findings:**
- Witness selection (`scoring.py:984–1000`) is explicitly *"always an independent OCR
  witness, never the extractor."* The independent sources are `doctr_full_run` /
  `doctr_bbox_run` (`refiner.py:49–52`), and the module header states it is
  *"pipeline-agnostic: it imports no DocAI Parse stage code."*
- All three reported table runs call it with `run_doctr_if_needed=True` and **no**
  `ocr_result` and **no** `witness_tokens`:
  `rescore_tables_crop.py:17` (RD-TableBench 287-subset ladder),
  `score_rocket_tables.py:38` (mortgage), `score_tables_other.py:34`.
  With no pipeline tokens passed, the code falls through to a **fresh docTR pass on the
  table crop** — a genuinely independent OCR run.
- The table **extractor is MinerU** (not docTR), so the docTR witness is a different
  engine from the extractor regardless.

**Answer:** the "independent OCR witness" claim is correct for every reported number. The
only wording to fix (it's imprecise, not wrong): drop *"distinct from the engine that
produced the pipeline's tokens"* in favour of *"independent of the extractor — a separate
docTR pass over the table region."* Our `ebv_paper_best.md` §3.5 already uses the safe
phrasing; the LaTeX should match it.

---

## 12d — Report NDA: the full stats you asked us to compute. **Done.**

**What you asked / why:** author decision A reverses C15 and reports NDA; you noted the
decision JSONLs were not in the repo and we must compute cluster CI, prior AUROC, presence
AUROC, and calibrated coverage.

**Correction:** the decision JSONLs **are** committed —
`experiments/unstructured_ntp/realkie_nda/decisions/realkie_nda_clean.jsonl` (148 scalar
field decisions, the canonical clean/untuned/binary split). Computed from it
(`experiments/unstructured_ntp/scripts/nda_stats.py`, sklearn tie-aware AUROC, doc-clustered bootstrap, and the exact
`calibration_coverage.py` method — 50/50 doc split, smallest calib threshold with ≤5% calib
error, 20 seeds):

| quantity | value |
|---|---|
| n (scalar field decisions) | 148 |
| base error | 8.8% (13 errors / 148) |
| **EBV AUROC** | **0.53** (0.5316) |
| **doc-clustered 95% CI** | **[0.34, 0.74]** |
| prior (empty-field) AUROC | **n/a** — `gt_empty_rate` non-null 0/148, no usable variance (same as FCC/Charities) |
| presence (value-in-source) AUROC | **0.70** |
| oracle cov@≤5% | 16% (stored 0.1622) |
| **calibrated cov@≤5%** | **11% (realised test error 5.5%)** |

So the Table 1 NDA row is: `148 | 8.8% | 0.53 (0.34–0.74) | — | n/a | 0.70 | 11% (5.5%)`.
§5.1 scientific reason (already in our draft): only 3 field types and 13 errors in 148
instances — too little label diversity for the classifier to learn.

**⚠ Note on the presence column for NDA (reporting choice, your call):** on every data-rich
domain EBV crushes the presence (value-in-source) baseline — 0.897 vs 0.53 (FCC), 0.96 vs
0.59 (S-1), 0.71 vs 0.53 (Charities). **NDA is the one flip: EBV 0.53 vs presence 0.70.**
The trivial "is the value on the page?" rule predicts correctness better than the trained
classifier there, because NDA is too small (3 field types, 13 errors / 148) for the
classifier to learn — it falls to near chance. It is the same "NDA is too small" story,
just stark. Printing 0.70 next to 0.53 visibly breaks the "EBV beats every baseline"
sentence **for that one row**, so: either show it (and scope the beats-baseline claim to the
data-rich domains) or leave NDA's presence cell blank (NDA stays the stated small-domain
negative). The number is **0.70** either way.

---

## 12i — Binary vs 3-tier, and safeguard firing (NDA). **Checked.**

**What you asked / why:** "catches 75–100%" (C13) came from `accept_3t`, but Method now
calls binary/best-model the main config — need to know which numbers are which, and how
often safeguards fire.

**Findings (NDA, from the same JSONL):**
- catch rate = **6/13 = 46% under *both* `accept_bin` and `accept_3t`** (3-tier only lowers
  accept-all coverage 55%→47%; it catches the same errors here).
- **Safeguards fire 0× on NDA**: `empty_prior_applied = 0`, `gated` (hard gate) `= 0`.
- AUROC itself is mode-independent (it ranks by the continuous `proba`), so the 0.53 stands
  regardless of binary vs 3-tier.

**Answer / flag:** two consistency points for you to resolve in the LaTeX, not reruns:
1. `ROBUSTNESS_EXPERIMENTS.md` states the canonical config is **binary**; if the paper's
   catch/coverage numbers were taken from `accept_3t`, re-state them from binary (or state
   explicitly that catch rates use the 3-tier operating point). For NDA it's moot (identical).
2. If NDA is now reported, the global **"catches 75–100%"** range no longer holds — NDA
   catches 46%. Either scope that phrase to the reported strong domains or widen the range.

---

## 12m — Baseline (prior / value-in-source) generation. **Already reproducible.**

The presence/prior baselines are not a missing script: they are columns in the committed
decision JSONLs (`signals.value_in_text`, `gt_empty_rate`). I reproduced both from them
above. If you want a standalone generator, `experiments/unstructured_ntp/scripts/nda_stats.py` shows the exact
computation (score direction: higher = more trusted; constant-prior → n/a; per-domain AUROC).
We can commit a cleaned version if you want it in-repo.

---

## Citations (you asked for MinerU version / HYCEDIS)

- **MinerU:** model `opendatalab/MinerU2.5-Pro-2605-1.2B` (a 1.2B VLM), via
  `mineru-vl-utils[transformers]==1.0.5` (`deploy/docker/requirements-mineru.txt`,
  `Dockerfile.mineru`). Cite as MinerU 2.5-Pro (1.2B), not generic "MinerU".
- **HYCEDIS:** already in our refs as Nguyen et al., 2022, **arXiv:2206.02628** (Document
  Intelligence Workshop @ KDD 2021 per the arXiv comment). Use the arXiv entry.

---

## Author decisions — resolved

- **A. Abstract coverage wording.** Resolved in main(3): the abstract **keeps** the coverage
  line, FCC-specific — "auto-accepts 81% of fields with 2.1% test error." Citing FCC (error
  safely 2.1%) sidesteps the Charities-misses-5% problem, so no range/soft-pedal/drop is
  needed. (Not dropped — kept, FCC-only.)
- **Abstract mention of NDA.** Resolved in main(3): the abstract already says "near chance on
  a small NDA set."
- **B. Table-label disclosure (C9).** Author decision: **B3** — present it as plain "ground
  truth," no LLM/annotator detail. If a phrase is wanted at all, use **"fixed rubric,
  adjudicated by the authors"** (or "…adjudicated by the correctness reviewer"). **Not** B2
  (do not mention "two LLMs").
- **12e — "evidence-cost ladder".** Handled on his side in main(3); no answer needed from us.
- **12g — witness independence.** Rechecked (see top): independent. Answer: confirmed.

Computations: `experiments/unstructured_ntp/scripts/nda_stats.py`. We left the paper drafts
unchanged — all computed numbers are in this doc for you to apply in your finalized version.
