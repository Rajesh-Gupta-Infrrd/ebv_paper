# Pending: port colleague's C fixes (ab549ac) into the LaTeX

Apply each item when the section-by-section writing pass reaches that section.
Source: `docs/ebv_paper.md` diff c510bd9..ab549ac and `docs/reviews/C_CLAIM_RESPONSE_2026-10-28.md`.

| # | Section | Change |
|---|---|---|
| 1 | 05_results Table 1 | FATURA `0.994 [0.865, 0.994]` → `0.95`; VRDU `0.896` → `0.92` (end-to-end, unplaced fields ranked lowest) |
| 2 | 05_results Table 1 caption | Drop FATURA bracket sentence; add "ROI AUROC counts every field, and fields the verifier cannot place are ranked lowest." |
| 3 | 05_results §5.1 | "0.71--0.99" → "0.71--0.96" (public fields max is now S-1 0.96); FATURA sentence → "On FATURA, EBV reaches 0.95 without an extra call." Drop Jin parity |
| 4 | 02, 04, 05 (6 places) | ConfBench logprob `0.58--0.64` → `0.59--0.64` (C1) |
| 5 | 02_related_work | Jin: "…on FATURA, with an optional second-VLM check"; "(e.g. the optional second-VLM check of Jin et al.)" (C2) |
| 6 | 04_setup GT | "human-verified value" → "finalised value, corrected by a person where a correction was needed" (C6) |
| 7 | 04_setup FATURA | "bracket the true AUROC" → "exact-match scoring wrongly fails some spatially correct values, which we relabel by containment (Appendix)" |
| 8 | 10_appendix | Replace [0.865, 0.994] sentence → "Table 1 counts every field and ranks fields the verifier cannot place lowest (0.95). On placed fields alone, AUROC is 0.994." |
| 9 | 05_results Table 3 | Closing disclosure 0.95 → 0.94 (learned ROI, C7) |
| 10 | 08_limitations (i) | Same GT wording as #6 |
| 11 | 08_limitations (ii) | Replace "do not re-run … natural addition" → "Token-logprob baselines come from a published benchmark on comparable fields, not from our splits, so that comparison is indicative." (B5) |
| 12 | 04_setup metrics | Add calibration protocol: document-level 50/50 calibration/test split, averaged over 20 seeds (C3) |
| 12b | 04_setup metrics | Moved out of the Intro on Oct 28: say per mode where the threshold comes from. Free-form fields: held-out calibration. ROI: coverage measured on test. Tables: the production threshold. Also replace "zero-cost signals" with "confidence signals the pipeline has without an extra model call" (Setup and Results) |
| 12c | 03–06, 08 | Terminology (Oct 28): "unstructured" replaces "variable-layout". The gloss "unstructured (variable-layout)" appears once, in Intro ¶4. Also replace "contract" with plain words (e.g. "the same accept-or-route decision") in the Method opening and §3.1 |
| 12d | 05_results Table 1 + §5.1, 00_abstract | **Report NDA (author decision A, Oct 28; reverses C15 for NDA).** Known numbers come from `experiments/ROBUSTNESS_EXPERIMENTS.md` §2: n=148, base err 8.8%, AUROC 0.53, oracle cov@5% 16%. **The colleague must compute** the cluster CI, prior and presence AUROC, and calibrated coverage (`calibration_coverage.py`). The decision JSONLs are not in the repo. §5.1 needs one sentence giving the scientific reason: 3 field types and 13 errors in 148 instances are too little label diversity to learn from. The abstract says "from AUROC 0.71 on long charity reports"; decide whether it should also say near chance on NDA. Intro ¶5 already does. |
| 12e | 03_method §cost | "we price it explicitly on the evidence-cost ladder" overclaims, because no latency or compute cost is measured. Say it is one extra OCR pass whose *gain* we measure, or add a latency number. Drop the coined term "evidence-cost ladder" (also in the §5.2 heading) |
| 12f | 04_setup metrics, 05_results §5.2 | Table threshold: Method and Intro say "the fixed threshold used in production" (memory: 85). Setup says "a threshold tuned for few false alarms". **Resolved (Oct 28):** `docs/_archive/ebv_method_versioning.md` says "≥85 accept is a documented production operating point". So fix Setup and Results to say production threshold (85/100), not "tuned" |
| 12g | 03_method §3.5, 01_intro | **Author to recheck.** Is the OCR witness independent? The archived notes say the witness first reuses the pipeline's own docTR tokens and runs docTR on the crop only if a flag is set. If the pipeline OCR was docTR for RD-TableBench or the mortgage tables, the claim "separate from the engine that produced the pipeline's tokens" must be qualified |
| 12h | 04_setup | State that results are per unit (fields, tables). There is no document-level experiment, because public sets lack mixed field+table outputs |
| 12i | 05_results / 06_analysis | Disclose how often each safeguard fires. The empty-field rule fires on S-1 only (3,083) and never on FCC, Charities or NDA. Hard gates fire on FCC (11) and S-1. Check which numbers use the binary best-model mode and which use the 3-tier (agreement) mode: C13 "catches 75–100%" came from accept_3t. Method now says binary/best-model is the main configuration and only mentions 3-tier as an option |
| 12j | done | Signal model chosen by accuracy on the labelled training data (author, Oct 28). Method updated. If it was a held-out part of the training data, the wording still holds |
| 12k | 05_results | The structure-only 0.76 re-fuses **4** HTML signals (geometry, token_shape, structural, reading_order; `INDIRECT_EXPERIMENTS.md:132`). The deployed scorer gives token_shape and reading_order weight 0. Say this in the Table 2 caption. Also define the 287-table subset (it is the set where the signals could be re-emitted) |
| 12l | 05_results Table 1 | Rename the "cov@≤5%" header to "coverage (test error)" or "calibrated coverage". The test error can exceed 5% (Charities 5.5%). Mark ROI coverage as a test-curve diagnostic |
| 12m | colleague | Commit the baseline (prior, value-in-source) generation script and outputs: score direction, constant-prior handling, per-domain AUROC |
| 13 | figures/fig_results.png | Copy regenerated `docs/figures/fig_results.png` (0.95 / 0.92 / 0.94) |

**Done on Oct 28 (04186be):** in 02_related_work, items #4 and #5 (C1 and C2), plus C11a, C11b and C12a–e. Item #4 (C1) still has to be applied in 04_setup and 05_results.

**Done on Oct 28 (e1b047e), 04_setup:**
- #4 (Setup part), #6, #7, #12, 12b (Setup part) and 12h.
- 12c and 12f (Setup parts).
- C14 dataset and extractor cites. The MinerU version still needs checking; there is a TODO in the file.
- NDA listed among the datasets.

**Remaining for Results:**
- #1, #2, #3, #4 (table and text), #9, #13, 12b ("zero-cost"), 12d, 12f (§5.2 text) and 12i.

## Open author decisions
- **A. Abstract X.** Calibrated coverage: FCC 81% (2.1%), S-1 100% (3.3%), Charities 79% (5.5%, misses 5%).
  A1 (rec.): "…auto-accepts 79–100\% of free-form fields, and their error stays at or below 5\% on two of three benchmarks." A2: "…at close to a 5\% error target." A3: drop sentence.
- **B. Table-label disclosure (C9).** B1 colleague's "fixed rubric, adjudicated by the authors"; B2 "pre-labelled by two LLMs and adjudicated by the authors under a fixed rubric"; B3 nothing.
- **Citations (C11/C12/C14), separate commit.** Need: MinerU version used; HYCEDIS arXiv vs Springer.

## Resolved, no change
C4 (S-1 split by filing, committed), C5 (empty prior fires on S-1, 3,083×), C3 (coverage already calibration-based).

**Done on Oct 28, 05_results:**
- #1, #2, #3, #4, #9 and #13 (new figure copied).
- 12b, 12d (NDA row with TODO), 12e (§5.2 heading), 12f, 12k and 12l. Bold removed.
- Results-section open questions moved to `QUESTIONS_FOR_COLLEAGUE_2026-10-28.md`.
- Still to do: §6 Analysis ("ladder", "free-form"), Conclusion ("free-form"), Limitations #10/#11, Appendix #8.
