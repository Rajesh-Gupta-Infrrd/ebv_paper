# Response to the C-claim review (C_CLAIM_DECISIONS_2026-10-27)

The reviewing agent saw only the GitHub repo (no datasets, results, or prior context), so several
items are based on incomplete information. Each claim below was cross-checked against the code and
stored results. Date: 2026-10-28.

## High-risk

- **C7 — ROI "uses the gold field box."** *Real but negligible.* `verify_rocket_fields.py:36-58`
  did compute the spatial feature against the test document's own gold box. Re-run with the region
  **learned from training folds only** (`verify_rocket_roi_learned.py`): URLA 0.952→**0.954**,
  CD 0.944→**0.939**, coverage unchanged (86% / 81%). Templated forms ⇒ learned region ≈ gold box.
  **Action:** adopted the learned-ROI version; paper Table 3 CD 0.95→**0.94**.

- **C8 — FATURA 0.994 excludes unscored fields.** *Real.* `run_roi.py:48` drops NaN wv_scores.
  End-to-end (unscored = lowest trust) = **0.952**; scored-only = 0.994. **Action:** report FATURA
  **0.95 end-to-end** in Table 1 (0.994 on scored fields kept in text, Jin comparison scoped to it).
  VRDU has the same mechanism; its end-to-end (0.920) is **higher** than located-only (0.896), so
  Table 1 VRDU 0.896 → **0.92** (end-to-end, for consistency with FATURA).

- **C3 — coverage swept on test, not a calibration split.** *Mostly misled.* The function they found
  (`domain_signal.py::_cov_at_risk`) is an auxiliary oracle sweep. The **reported** coverage numbers
  are calibration-based: a real calib/test split (`calibration_coverage.py`) reproduces them —
  **S-1 100% @ 3.2% risk, Charities 79% @ 5.5% risk**, matching the paper's parentheticals.
  **Action:** committed `calibration_coverage.py`; no wording change.

- **C6 — GT is not "human-verified."** *Real (benign).* `pull_rocket_gt.py:32-34`: GT =
  `correctedValue` when present, else the extracted `value` (i.e. the value was already correct, so
  no correction exists). **Action:** wording → "the production system's finalized value
  (human-corrected where a correction was needed)."

- **C9 — state the table-label method.** Author decision: keep plain "ground truth"; a generic
  neutral line is drafted if the submission requires stating the evaluation method. **No VLM/κ
  disclosure.**

- **C4 — "S-1 split by page (filing leakage), not committed."** *Incorrect — their agent missed it.*
  Train/test filings have **0 overlap** (`train.csv` vs `test.csv` by `original_filename`), and the
  **filing-grouped run is committed**: `realkie_s1/bundle_clean/{test,fold}_metrics_s1_filing.csv`
  (catch 94.5%, NTP accuracy 99.7%, consistent with ~0.96). No leakage; no change.

## Medium-risk

- **C5 — "empty-field prior never fires, delete it."** *Incorrect — incomplete info.*
  `empty_prior_applied` = 0 on FCC/Charities/NDA but **= 3083 on S-1** (`realkie_s1/.../UNSTRUCTURED_realkie_s1.md:51`),
  where the prior is the single most load-bearing feature. **Clause kept.**

- **C10 — adjudication log.** Paper claim is correct; only the 6 Signal cases lack saved image crops
  (verified from pred/GT/text). Repo-completeness nit, **no paper change**.

- **C1 — ConfBench logprob 0.58→0.59.** Applied (0.59–0.64) per their citation check.

- **C2 — Jin "two-VLM comparison."** Pending author decision (→ "optional second-VLM check").

- **C15 — add omitted-negatives line (NDA/OmniDoc).** Author decision: **not added.**

- **C13 — "catches 75–100%."** Sourced in our version (per-leg caught@deployed under accept_3t);
  their `main.tex` diverged. **Kept.**

- **B5 — logprob "not run."** Limitations reworded to the "indicative, from a published benchmark"
  framing.

## Low-risk (citations C11/C12/C14)
Deferred to the LaTeX pass (outside the HTML/MD repo).

## Outside the paper
- **Repo is not anonymous** (company/product/DB/author in commits, filenames, paths) — do **not**
  link it in a double-blind submission; use an anonymized supplementary zip.
- Data-use clearance for aggregate results: author-confirmed.
