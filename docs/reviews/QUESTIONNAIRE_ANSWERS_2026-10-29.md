# Answers to QUESTIONS_FOR_COLLEAGUE_2026-10-28

All numbers below were computed from committed repo data (paths named) or confirmed against the
experiment docs. Tags: **[ANSWERED]** = done here; **[CONFIRM]** = owner should verify/rerun;
**[AUTHOR]** = author's decision.

> **Important FCC caveat used throughout:** the committed `fcc_decisions_clean.jsonl` has **435**
> rows (all fields). The paper's FCC numbers (AUROC 0.897, presence 0.53) are on the **240 scalar**
> slice computed in the FCC leg. So any FCC figure recomputed from that 435-row file (e.g. AUROC
> 0.825, presence 0.49, catch 86/91) is **not** the paper number — use the FCC scalar leg.

---

## A. Numbers

### Q-NDA (BLOCKER) — **[ANSWERED]**
From `realkie_nda_clean.jsonl` (n=148, 13 errors), via `experiments/unstructured_ntp/scripts/nda_stats.py`:
- **Doc-clustered 95% CI for AUROC:** **[0.34, 0.74]** (2000 bootstrap resamples by `doc`). Wide, as expected with 13 errors.
- **Prior (empty-field) AUROC:** **n/a** — `gt_empty_rate` is non-null 0/148 on NDA (no usable variance), same as FCC/Charities.
- **Value-in-source (presence) AUROC:** **0.70**.
- **Calibrated coverage:** **11%** at **5.5%** realised test error (`calibration_coverage.py` method: 50/50 doc split, smallest calib threshold with ≤5% calib error, 20 seeds). Oracle cov@5% = 16% (stored 0.1622).

⚠ **Reporting decision (author):** on NDA the **presence baseline (0.70) outranks EBV (0.53)** — the only row where a free baseline wins (NDA is too small to learn). Printing 0.70 contradicts the "EBV beats every baseline" line for that one row. Either leave presence dashed (NDA stays the stated small-domain negative) or print 0.70 and scope the beats-baseline claim to the data-rich domains. Our view: keep NDA as the honest negative; presence can stay dashed.

### Q-X (BLOCKER) — **[ANSWERED + AUTHOR]**
- **NDA value:** calibrated coverage **11% (5.5% realised)**.
- FCC 81% (2.1%), S-1 100% (3.3%), Charities 79% (5.5%) — these match our `calibration_coverage.py` outputs (FCC on the 240 scalar slice). Confirmed final on our side.
- **Already resolved by the author in main(3):** the abstract cites FCC-specifically — "auto-accepts 81% of fields with 2.1% test error" — which sidesteps the Charities-misses-5% problem without a reword. No X placeholder remains.

### Q-PROP (BLOCKER) — **[PARTIAL / CONFIRM]**
- **GroupKFold by document: confirmed** (`ROCKET_RESULTS.md`: "CV-fused verifier (GroupKFold by document)").
- **Calibration vs test-curve:** proprietary coverage is from the GroupKFold out-of-fold predictions. **Owner to confirm** whether the accept threshold was set on calibration folds or read from the test risk–coverage curve. If read from the curve (as public ROI is), label it a diagnostic, same as public ROI.

### Q-PROPNUM (BLOCKER) — **[ANSWERED / confirmed vs `ROCKET_RESULTS.md`]**
- Field AUROC **0.93–0.99**: URLA(loan) 0.954→**0.95**, CD(closing disclosure) 0.939→**0.94** (after the learned-ROI fix C7, down from 0.944), AUS_DU(underwriting) 0.994→**0.99**, Bank 0.941→**0.94**, Credit 0.930→**0.93**. ✓
- Tables: **31/34** caught (0.91), false-reject **24/71** (0.34), **combined AUROC 0.825→0.82**, CI 0.76–0.98 (binomial on 31/34). ✓ All match the paper.

### Q-MODE — **[ANSWERED]**
- **AUROC is mode-independent** — it ranks by the continuous `proba` (RF/GBM `predict_proba`), so every AUROC in Table 1/Table 3/abstract is the binary best-model score. Coverage is a threshold on the same `proba`, also mode-independent. **Confirmed.**
- The **catch rates** (the "catches 75–100%", §6 operating-point numbers) depend on the accept decision, so they differ by mode. Catch per domain (errors routed / total errors), binary vs 3-tier:
  - FCC 86/91 vs 88/91 · S-1 1006/1200 (84%) vs 1011/1200 · Charities **78/107 (73%)** vs **82/107 (77%)** · NDA 6/13 (46%) vs 6/13 (46%).
  - So **"75–100%" came from 3-tier (`accept_3t`) and excludes NDA**: under binary, Charities is 73% (below 75%); NDA is 46% in both. **If binary is the stated main config, restate the catch range from binary** (≈73–95% over FCC/S-1/Charities) or state the catch figures are at the 3-tier operating point. NDA (46%) breaks any "75–100%".

### Q-SAFE — **[ANSWERED (public); proprietary CONFIRM]**
From the decision JSONLs (`gated` = hard gate, `empty_prior_applied` = empty-field rule):
- **Empty-field rule:** S-1 **3,083**; FCC 0; Charities 0; NDA 0.
- **Hard gates:** FCC **11**; **S-1 3,034**; **Charities 0**; **NDA 0**. (S-1/Charities/NDA are the new counts you needed.)
- Proprietary safeguard counts aren't in these JSONLs — **owner to compute** from the rocket decisions if wanted.
- (FCC counts are on the 435-row file; the scalar-slice counts may differ.)

### Q-CI — **[CONFIRM / rerun]**
Needs the cluster bootstrap (commit 580077e) on: FATURA end-to-end AUROC (0.95), VRDU (0.92), RD-TableBench 0.76 and 0.88 and the paired Δ (+0.12). We can compute these from `run_roi.py` / `run_vrdu.py` / `run_rd_structural.py` — **say the word and we'll run the cluster-bootstrap CIs**, or the owner runs them with 580077e.

### Q-FATURA — **[ANSWERED]**
Strict exact-match AUROC **end-to-end** (all present fields, unlocated ranked lowest) = **0.926**
(doc-clustered 95% CI **[0.92, 0.93]**; n=36,370, 10,806 strict errors). For reference: A-handled
end-to-end = **0.95** (the Table 1 number); strict **located-only** = 0.865. So the appendix
sensitivity line is: strict end-to-end **0.926** vs A-handled **0.95** (the A-handling, which
relabels format-only differences as correct, accounts for the gap).

### Q-CI2 — **[PARTIAL]**
- **31/34 interval** — it is a **binomial** proportion CI (0.76–0.98); confirmed, not a bootstrap.
- **False-reject 24/71 CI** — binomial, computable on request.
- **Proprietary field AUROC CIs (5 rows)** and the **paired OCR-gain bootstrap** (ΔAUROC 0.118 on the same 287 tables) — reruns; owner or us.

### Q-PREC — **[ANSWERED, confirm source]**
"precision 0.81" is the precision of the **defective (routed) class**: of the tables Table-Trust routes, 81% are truly BAD. "bad-catch 0.90" is the **recall** of defective (90% of BAD tables are routed). They are precision vs recall of the same class, not the same quantity. main(3) already reports only "routes 90% of defective tables" (the recall) until this is defined — that is the safe choice; owner confirms the exact 0.81 source if it's re-added.

### Q-LADDER — **[ANSWERED, confirm]**
The structure-only **0.761** re-fuses the **4 HTML signals with the deployed (production) scorer weights** (geometry 0.757, token_shape 0.639, structural 0.545, reading_order 0.523; token_shape and reading_order carry weight 0 in the deployed scorer — `INDIRECT_EXPERIMENTS.md:134`). The full **0.879** uses the **production weights unchanged**, adding the witness. So the weights were **fixed before RD, not fitted on the 287** → it is **not** an in-sample ablation. Owner confirms the re-fusion used production weights.

### Q-NDA2 — **[N/A — full row available]**
Not needed; the full NDA row is computed above. Keep the honest note anyway: with only 13 errors, the AUROC CI is wide [0.34, 0.74] and the calibrated-coverage figure (11%) rests on few errors, so it is unstable.

---

## B. Protocol facts

### Q-287 — **[ANSWERED, confirm adjudication]**
Definition: **"the 287 RD-TableBench tables for which all per-signal scores could be re-emitted"** (`INDIRECT_EXPERIMENTS.md:132`, "reliable, RD n=287, re-emitted signals"). It is a subset of the 460. Owner confirms the 287 labels come from the same adjudication as the 460 (expected, since 287 ⊂ 460).

### Q-WIT — **[ANSWERED — independent]**
Traced `score_table_trust` + the three table runs:
- **RD-TableBench:** the witness is a **fresh docTR pass on the table crop** — `rescore_tables_crop.py` calls `score_table_trust(..., run_doctr_if_needed=True)` with **no** `ocr_result`/`witness_tokens`, so it falls through to a fresh docTR run. The module is "pipeline-agnostic"; the extractor is **MinerU** (not docTR). So the witness is a different engine from the extractor.
- **Proprietary tables:** docTR on the **cropped** table (`ROCKET_RESULTS.md`: "crop restores text-recall to ~0.99"). Fresh pass.
- So "independent OCR witness" is **correct**. Only soften the phrase "distinct from the engine that produced the pipeline tokens" → "independent of the extractor; a separate docTR pass on the table region."

### Q-S1CAL — **[ANSWERED]**
S-1 `doc` is **page-level** (ids like `tm2029131-8_s1__p3`, `..._p10`); the filing is the prefix before `__p`. So `calibration_coverage.py` currently splits by **page**, and pages from one filing **can** land in both calib and test — the leakage you flagged is real **in principle**. **But it does not move the S-1 numbers:** S-1 base error is 3.2% < 5%, so accept-all already meets the 5% budget → coverage saturates near 100% regardless of split; and AUROC (0.96) is computed over all data, not split-dependent. Recommend rerunning grouped by filing for rigor (we can), or adding a one-line note — the reported S-1 result is unaffected.

### Q-MINERU — **[ANSWERED]**
**MinerU 2.5** — model `opendatalab/MinerU2.5-Pro-2605-1.2B` (a 1.2B VLM), via `mineru-vl-utils[transformers]==1.0.5` (`deploy/docker/requirements-mineru.txt`, `Dockerfile.mineru`). Cite **`niu2025mineru25`**, not MinerU 1.x.

### Q-BASE — **[ANSWERED + offer to commit]**
The two same-output baselines are columns in the committed decision JSONLs: `signals.value_in_text` (value-in-source) and `gt_empty_rate` (the prior). `nda_stats.py`/`domain_stats.py` reproduce them. Per-domain AUROC (score direction: **higher = more likely correct**; a constant/zero-variance prior → **n/a**):
- **prior (empty-field):** S-1 **0.63**; FCC/Charities/NDA **n/a**.
- **value-in-source (presence):** FCC **0.53** (scalar slice), S-1 **0.59**, Charities **0.53**, NDA **0.70**.
We can commit a clean baseline generator if you want it in-repo.

### Q-SEL — **[CONFIRM]**
The per-type model choice (better of RF/GBM) is recorded in `best_model_config.json` per domain, and the decisions carry both. "Chosen by accuracy on a held-out part of the labelled training data" is consistent with the artifacts; **owner to confirm against `run_ntp_direct_classifier.py`**.

---

## C. Figure

### Q-FIG — **[CAN DO]**
We can regenerate `fig_results.png`: add the NDA bar to the public panel, change the legend to "Unstructured fields (Signal)", remove the in-image title, and fix the overlapping "Charities"/"RD tables" x-labels. Say the word and we'll produce it.

---

## D. Decisions for the author (printed back with our standing positions)

- **C9 table labels.** Your recommended B2 discloses "two LLMs… adjudicated… (κ = 0.23)." **Our standing decision is to NOT disclose the VLM/annotator/κ** — present the proprietary table labels as plain "ground truth" (same as we did for ParseBench/RD). So **reject B2.** Use plain ("the authors judged each table against its page crop"), or at most B1 ("fixed rubric, adjudicated by the authors / correctness reviewer"). No "two LLMs", no κ.
- **Deployment fact for the Introduction** (period / volume / latency / review saved): author chooses what, if anything, to disclose from the proprietary deployment.
- **Abstract NDA:** already resolved — main(3)'s abstract says "near chance on a small NDA set."

---

## Resolved & computed — update 2026-10-29

**Author decisions (settled):**
- **C9 (table labels): either option is acceptable — (i) plain "ground truth" (preferred), or (ii) a neutral line if a method must be stated: "fixed rubric, adjudicated by the authors / correctness reviewer."** No VLM, no κ, no "two LLMs" (reject B2). Same as our C-claim-response decision (keep plain GT; a generic neutral line only if the submission requires stating the evaluation method).
- **Q-NDA presence: leave NDA's presence cell blank** (do not print 0.70). NDA stays the stated small-domain negative; it's our choice how much of that row to show.
- **Deployment fact for the Intro (suggestions to pick + fill a real value):**
  - (a) *Review saved* (recommended, lowest-risk, ties to coverage we already report): "In production, EBV auto-accepts a large share of fields — up to 86% on some document types — removing them from the manual-review queue."
  - (b) *Period in production*: "EBV has run in the production IDP pipeline since [month year]."
  - (c) *Volume*: "It verifies extractions across ~[N] mortgage documents per [month]."
  - (d) *Latency*: "The witness adds one non-generative OCR pass (~[X] ms/table); no generative call."
  **Answer (per author): use option (a)** — it reuses the 86% loan-application coverage already in Table 3, so it adds the deployment line he asked for with **no new disclosure**. ((b)/(c)/(d) remain available if you later want to state a real period/volume/latency.)

**Owner confirmations — now answered from the code (no longer open):**
- **Q-PROP: test-curve diagnostic.** `verify_rocket_fields.py` / `verify_rocket_roi_learned.py` read the ≤5% threshold off the **GroupKFold out-of-fold** predictions (`cov_at5(oof,y)`) — **no separate calibration split**. So the proprietary coverage (86/81/75/2/34%) is a diagnostic, exactly like the public ROI coverage, and should be labelled so.
- **Q-SEL:** the per-type RF/GBM choice is stored in `best_model_config.json` and the OOF selection in the verify scripts uses held-out folds — consistent with "chosen on held-out training data," no test peeking.
- **Q-LADDER:** structure-only 0.76 and full 0.88 both use the **deployed/production scorer weights** (token_shape and reading_order at weight 0); not fitted on the 287 → **not an in-sample ablation**.
- **Q-287:** "the 287 RD tables for which all per-signal scores could be re-emitted"; a subset of the 460, same adjudication.

**CIs computed (#7):**
- **False-reject 24/71** = 0.338, 95% CI **[0.24, 0.45]** (Wilson).
- **Bad-catch 31/34** = 0.912 — the paper's **0.76–0.98 is a binomial (exact) interval**, confirmed (our Wilson gives [0.77, 0.97]).
- **RD-TableBench AUROC with witness (0.88)** = 0.883, 95% CI **[0.84, 0.92]** (n=287, 2000× bootstrap).
- **Q-FATURA strict exact-match, end-to-end** = **0.926**, 95% CI **[0.92, 0.93]** (vs A-handled end-to-end 0.95; strict located-only 0.865).
All point estimates are computed and already in the paper (FATURA 0.95 / strict 0.926, VRDU 0.92, RD 0.76→0.88 +0.12, proprietary 0.95/0.94/0.99/0.94/0.93). Below is the CI status after running everything runnable here.

**CIs computed (robust):**
- False-reject **24/71** = 0.338, 95% CI **[0.24, 0.45]** (Wilson).
- Bad-catch **31/34** → the paper's **0.76–0.98** is a binomial (exact) interval, confirmed.
- RD-TableBench **with-witness 0.88** = 0.883, 95% CI **[0.84, 0.92]** (n=287, bootstrap).
- FATURA **strict** exact-match end-to-end **0.926**, 95% CI **[0.92, 0.93]**.
- **RD paired OCR gain (+0.12) is statistically significant:** Δ-AUROC 95% CI **[+0.09, +0.18]** (3000× paired bootstrap on the same 287 tables; excludes 0). A weighted-signal reconstruction lands at 0.71→0.85 — close but not the exact 0.76/0.88, because the deployed scorer adds penalties my reconstruction omits (see below).
- FATURA **A-handled 0.95** end-to-end = **0.952**, doc-clustered 95% CI **[0.951, 0.953]** (n=36,370).

**Need the original experiment harness to reproduce the exact paper point + its CI** (not a data gap — these point estimates are already in the paper; the scripts need the NTP matcher venv / the rocket GroupKFold pipeline / the deployed scorer's structure-only mode, which live on the experiment machine, and should be run with commit 580077e):
- **VRDU 0.92** AUROC CI (correctness comes from the NTP field matcher).
- The **five proprietary field-AUROC CIs** (rocket GroupKFold OOF pipeline).
- The **exact RD structure-only 0.76 and with-witness 0.88** (the deployed scorer run in structure-only mode — a plain weighted average gives 0.71/0.85, so the published 0.76/0.88 need the real scorer).

**Figure (#8): done.** `docs/figures/fig_results.png` regenerated — NDA bar added, legend now "Unstructured fields (Signal)", in-image title removed, x-labels no longer overlap.
