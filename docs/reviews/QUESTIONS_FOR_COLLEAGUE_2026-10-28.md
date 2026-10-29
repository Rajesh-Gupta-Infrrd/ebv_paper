# EBV paper: open questions for the experiments owner

Date: 28 Oct 2026. Deadline: 31 Oct 2026, 11:59pm AoE.
Branch: `naacl-latex` in `ebv_paper`. Section files are in `ebv_latex/sections/`.

Please answer under each item, or reply with a commit hash. Each item names the text that depends on it. Items marked **BLOCKER** hold numbers that are printed in the paper.

---

## A. Numbers to compute or confirm

### Q-NDA. NDA row in Table 1 (BLOCKER)
- The paper now reports NDA. The author decided to report the negative result, which reverses C15 for NDA only.
- The repo has n=148, base error 8.8% and AUROC 0.53, from `experiments/ROBUSTNESS_EXPERIMENTS.md` §2.
- **Needed:**
  1. A document-clustered 95% CI for the AUROC.
  2. The AUROC of the per-field prior and of value-in-source on NDA.
  3. Calibrated coverage and realised test error from `calibration_coverage.py`.
- **Where it goes:** `05_results.tex` Table 1, row "NDA". It currently shows "---".

### Q-X. Abstract coverage number X (BLOCKER)
- The abstract says "With a threshold set on held-out calibration data, EBV auto-accepts X% of fields while keeping their error at or below 5%."
- The calibrated numbers are FCC 81% (2.1%), S-1 100% (3.3%), Charities 79% (5.5%) and NDA (?).
- Charities misses the 5% target, so the sentence will be reworded. **Please confirm** these three numbers are final, and give the NDA value.

### Q-PROP. Proprietary coverage protocol (BLOCKER)
- Table 3 shows field coverage of 86 / 81 / 75 / 2 / 34%.
- **Were these thresholds set on calibration folds, or read from the test risk–coverage curve?**
- If they were read from the test curve, we must label them as a diagnostic, as we already do for public ROI.
- Also confirm that the proprietary verifiers were trained with GroupKFold by document, as `ROCKET_RESULTS.md` says.

### Q-PROPNUM. Proprietary numbers after the metric fixes
Please reconfirm each of these. They are printed in the Introduction, Table 3 and §5.3:
- field AUROC 0.93–0.99, with closing disclosure at 0.94 after the learned ROI;
- tables: 31/34 caught, false-reject rate 24/71, combined AUROC 0.82 and CI 0.76–0.98.

There is a TODO in `01_introduction.tex`.

### Q-MODE. Which Signal mode produced each number
- Method now says the main configuration is the binary mode, using the better of RF/GBM. Its `predict_proba` is the trust score.
- The old "catches 75–100%" claim (C13) came from `accept_3t`, the stricter mode where both models must agree.
- **Confirm** that every AUROC and coverage number in Table 1, Table 3 and the abstract comes from binary best-model scores.
- **List** any number that comes from 3-tier, including catch rates in §6 Analysis.

### Q-SAFE. How often the safeguards fire
- Results or Analysis should disclose how often the hard gates and the empty-field rule change a decision, per benchmark.
- Known: the empty-field rule fires 3,083 times on S-1 and 0 times on FCC, Charities and NDA. Hard gates fire 11 times on FCC.
- **Needed:** the hard-gate count on S-1, Charities and NDA, and on the proprietary types if available.

### Q-CI. Missing confidence intervals
Setup promises document-clustered 95% CIs for the main comparisons. **Needed:**
- FATURA end-to-end AUROC (0.95);
- VRDU end-to-end AUROC (0.92);
- RD-TableBench AUROC 0.76 and 0.88, and the difference between them. The +0.12 OCR gain is a headline claim.

Please use the corrected cluster bootstrap from commit `580077e`.

### Q-FATURA. Strict exact-match AUROC, end to end
- The appendix will report the strict exact-match result as a sensitivity check.
- We only have 0.865, which counts located fields only.
- **Needed:** strict exact-match AUROC over all present fields, with unlocated fields ranked lowest, so it matches the 0.95.

---

### Q-CI2. More intervals (second review)
- **Proprietary field AUROCs.** Document-clustered CIs for all five rows of Table 3, since there are many fields per document.
- **31/34.** Which method produced the 0.76–0.98 interval? The paper now says "binomial". Please confirm, or correct it.
- **False-reject rate 24/71.** Please give its 95% CI.
- **OCR gain.** A paired bootstrap CI on the same 287 tables for ΔAUROC = 0.118 (0.761 → 0.879).

### Q-PREC. "Precision 0.81" on RD (460 tables)
- Which class is this the precision of? Is it the share of routed tables that are defective, or the precision of predicting GOOD?
- `TABLES_EXPERIMENT.md` also lists recall 0.86 next to bad-catch 0.899, so these may be different quantities.
- The paper now reports only "routes 90% of defective tables" until this is defined.

### Q-LADDER. Weights for the structure-only row
- Who set the fusion weights for the 4-signal structure-only score (0.761)?
- Were they fixed before the RD evaluation, or fitted on the 287 labels?
- Does the full 0.879 use the production weights unchanged?
- If the weights were fitted on the 287 labels, the paper must call the result an in-sample ablation.

### Q-NDA2. If the NDA row cannot be completed
- The fallback is to report only n, base error and AUROC.
- Add a note that 13 errors are too few for stable calibrated coverage.
- Please still give the AUROC CI. With 13 errors it will be wide, and it matters.

## B. Protocol facts to confirm

### Q-287. The 287-table RD subset
- What exactly defines it? `INDIRECT_EXPERIMENTS.md:132` calls it "reliable, RD n=287, re-emitted signals".
- We need one sentence for the paper, e.g. "the 287 tables for which all per-signal scores could be re-emitted".
- Also confirm that the 460-table labels and the 287-table labels come from the same adjudication.

### Q-WIT. Is the OCR witness independent of the pipeline OCR?
- The archived notes say the witness first reuses the pipeline's own docTR tokens, and runs docTR on the table crop only if a flag is set.
- `ROCKET_RESULTS.md` says the proprietary witness was docTR on the cropped table.
- **For RD-TableBench and for the proprietary tables:** which OCR produced the pipeline tokens, and did the witness run a fresh docTR pass on the crop?
- The paper calls it an "independent OCR witness". If it reused the same engine's tokens, we must qualify that.

### Q-S1CAL. S-1 calibration splits
- `calibration_coverage.py` splits by `d["doc"]`. For S-1, is `doc` a page or a filing?
- If it is a page, the calibration and test halves share filings. Please rerun the calibration grouped by filing, or confirm that the difference is negligible.

### Q-MINERU. MinerU version (C14)
- Which MinerU version produced the tables: MinerU 1.x (`wang2024mineru`) or MinerU2.5 (`niu2025mineru25`)?

### Q-BASE. Baseline scripts (12m)
- Please commit the script and outputs for the two same-output baselines, per-field prior and value-in-source.
- For each, state the score direction, how a constant prior is handled, and the per-domain AUROC.
- Reviewers have asked for this.

### Q-SEL. Signal model selection
- The author says the better RF/GBM model is chosen by accuracy on a **held-out part of the labelled training data**. Method now says so.
- Please confirm this against `run_ntp_direct_classifier.py`.

---

## C. Figure

### Q-FIG. Regenerate `fig_results.png`
- Add an NDA bar to the public panel.
- Change the legend "Variable-layout fields (Signal)" to "Unstructured fields (Signal)".
- Remove the in-image title, because the caption already says it.
- Fix the overlapping "Charities" and "RD tables" x-labels.

---

## D. Decisions for the author (not the colleague)
- **C9 table labels.** Recommended wording (B2): "On RD-TableBench, whose own ground truth is often wrong, the authors judged each table against its page crop. Proprietary tables were labelled blind by two LLMs and adjudicated by the authors under a fixed rubric (κ = 0.23 before adjudication)."
- **Deployment fact** for the Introduction: one of period, volume, latency or review saved.
- **Abstract NDA.** Should the abstract say "near chance on NDA"?
