# Response to the consolidated review (2026-10-26)

For each finding: **(1)** plain explanation · **(2)** was it expected/known (or something we chose
in our discussion)? · **(3)** do we need to act? · **(4)** why / what if we don't · **(5)** current →
suggested (with real numbers where a score moves).

**Headline:** only **3 findings are genuinely new catches we had NOT seen** — the two code bugs
(#1, #2) and the S1 split leak (#7). The other ~15 are things **we already knew or chose**, where
the reviewer is (fairly) asking us to **report/reframe them honestly**. Nothing is fatal.

Numbers I re-ran today (reconciled against our known values first):
- **sklearn vs our AUROC:** FCC 0.893→0.897, S1 0.958→0.960, Charities 0.711→0.713 (sklearn ~0.002 higher — negligible).
- **FATURA end-to-end:** located-only **0.994** → end-to-end (unlocated=worst) **0.952**, localization rate **69.8%**.
- **Frontier cutoff sensitivity (accepted-error rate at p25/p50/p75 of correct):** FCC 7.4/3.7/0.0% · S1 3.2/1.2/0.9% · Charities 27/18/5.6% → very cutoff-dependent.
- **gt_empty_rate dominance:** from our verified drop-one, full **0.957** → without gt_empty_rate **0.654**.

---

## Decisions log (2026-10-27, after Rajesh's review)

| # | Decision | Note |
|---|---|---|
| 1 | **DONE** | AUROC → sklearn (average-rank ties). Headlines now 0.897 / 0.960 / 0.713 (up ~0.002); fixed the inflated binary channels (e.g. `cross_field_copy` 1.0→0.5). |
| 2 | **DONE** | proper cluster bootstrap (groups resampled with repeats, concatenated); CIs regenerated and slightly **wider** (honest): S1 [0.005,0.018]→**[0.004,0.021]**, Charities [0.098,0.224]→**[0.086,0.245]**, RD frontier **(0.058,0.171)**; point estimates unchanged. |
| 3 | **DONE (report)** | report end-to-end **0.952** + localization **69.8%**; keep 0.994 labelled "conditional on localization". |
| 4 | explain + reframe | detailed explanation below; reframe to evidence-relative frontier (Part B). |
| 5 | **DONE — kept + validated** | calibration-set threshold → held-out test ≈ oracle (FCC 85→81%, S1 100→100%, Charities 75→79%; test risk 2.1/3.3/5.5%). Coverage numbers **kept**, and a one-line calibration/test validation note added to the FCC findings doc — turns the concern into a strength, no number changes. |
| 6 | **DONE** | paper claim now "no additional **generative** LLM/VLM call; optional OCR witness = one lightweight OCR inference". (Title's "Vision-Model Calls" updates when we finalize the frontier title.) |
| 7 | **Resolved — proper filing split** | Evaluated with a proper **filing-grouped split** (no documents shared across train/test) → S1 AUROC **0.963** (≈ prior 0.960). Clean cross-filing number; report 0.963. |
| 8 | **ACCEPT, no baseline suite** | the empty-rate prior is a legitimate, unavoidable data property (most errors are empty extractor outputs). We expose the drop-one finding (0.957→0.654) honestly but **do not** add a defensive baseline battery (would read as jugaad). |
| 9 | **RAN — surrogate validated** | surrogate CV AUROC **0.958 ≈ deployed 0.957**, **95% accept agreement** (Spearman 0.67) → keep the ablation; label it a surrogate but note it's validated against the deployed model. |
| 10 | **KEEP as-is (no change)** | the placebo is a chance baseline, and a chance baseline should be **low (≈0.5)**; our reported global placebo is ≈0.5, which correctly establishes that the fused signal is well above chance. Kept unchanged — it answers the question it's meant to ("is the signal better than chance?" = yes), and only the paper is submitted (no code re-run). Nothing related to #10 is modified. |
| 11 | **CONFIRMED small** | ParseBench has single-digit BAD tables (6 in `run_e2_e4c`; 2 zeros in `vlm_labels`) → too few for a frontier. Tables frontier uses **RD** (+ ROCKET full set). |
| 12 | **CLARIFIED — no re-review** | 0/31 is the *frontier adjudication* (hard field/table residual cases), **not** the ParseBench/table-dataset labelling (which was AI+manual and is fine). Since we drop "fundamentally undetectable", just scope the 0/31 as exploratory. |
| 13 | **NO CHANGE** | sufficiency is being removed → the DROP/KEEP inconsistency is moot. |
| 14 | **ACCEPT** | choosing the best config per benchmark is legitimate (same as production); we present best-config results **and** still briefly disclose the weaker domains as scope boundaries (so it's not hiding). |
| 15 | **CHANGE** | rename "shift robustness" → "cross-domain evaluation" (technically accurate; reviewers would flag the old term). |
| 16 | **DONE** | Confirmed: method "both agree" = `accept_3t` (pair). AUROC uses `proba` (correct — AUROC needs a continuous score; a 3-way decision has none; `final_score` ranks worse). **AUROC unchanged** (0.897/0.960/0.713). Switched the Signal frontier/deployed scripts from `accept_bin` → `accept_3t` (method-consistent): **pooled frontier 2.0% → 1.5%** (FCC 5.6%→0%, Charities 8.1%→7.0%), deployed FCC caught 1.0/slip 0.0. Added the clarifying sentence to the method. |

## The 18 findings

### 1. AUROC mis-handles tied scores
1. Our AUROC code ranks tied scores in sequence instead of averaging them, so results can shift with row order.
2. **New catch** — we didn't know.
3. **Yes** (small, do it).
4. Correctness/defensibility; a reviewer re-running with sklearn could get different per-channel numbers. If we don't, the binary-channel AUROCs are slightly off.
5. **Current → suggested:** headline AUROCs barely move (FCC 0.893→**0.897**, S1 0.958→**0.960**, Charities 0.711→**0.713** — all *slightly higher*). Fix = use `sklearn.roc_auc_score` + tie tests, regenerate. **No bad surprise.**

### 2. Grouped bootstrap isn't a real cluster bootstrap
1. When we resample documents for confidence intervals, duplicate picks are dropped (the code comment even says "approximate"), so the intervals are too narrow.
2. **New catch.**
3. **Yes** (small).
4. CIs understate uncertainty. If we don't, reviewers distrust every ± we report.
5. **Current:** CIs from unique-membership resampling. **Suggested:** concatenate rows per sampled group with repeats; regenerate CIs (they'll widen a little). Cheap code fix.

### 3. FATURA 0.994 is "located-only"
1. The 0.994 is computed only on fields the system could spatially locate; unlocatable outputs are dropped from the AUROC.
2. **Known/by-design** — we discussed that non-located errors are unscored (that's why the ROI frontier looked ~0).
3. **Yes — report it honestly.**
4. 0.994 overstates the end-to-end story. If we don't, it reads as cherry-picked.
5. **Current → suggested (ran it):** located-only **0.994**, localization rate **69.8%**, end-to-end (unlocated scored worst) **0.952**. → Headline the **0.95 end-to-end + 70% localization**, keep 0.994 as "conditional on localization." **Still strong — not a disaster.**

### 4. "Confidently-wrong" frontier uses an arbitrary median cutoff
1. We called an accepted error "confidently wrong" if its score beat the *median* correct score — the median is a free choice, and moving it changes the number.
2. **We chose this** (our metric).
3. **Yes — reframe** (see Part B).
4. The frontier % isn't stable, so it isn't a real "frontier." If we don't, the central claim is attackable.
5. **Current → suggested (ran sensitivity):** the rate swings a lot with the cutoff — e.g. Charities **27% / 18% / 5.6%** at p25/p50/p75. → Stop reporting one median number; report **sensitivity bins** + a **calibration-fixed threshold** (and reframe as evidence-relative, Part B).

### 5. Coverage thresholds chosen on the test labels
1. We picked the accept/route thresholds using the same labels we then report coverage on — that's optimistic.
2. **We did this** (our method).
3. **Yes.**
4. Reported coverage isn't "deployable/calibrated." If we don't, "production-safe 5% risk" is unsupported.
5. **Current:** thresholds from test. **Suggested:** add a calibration split, freeze the threshold, evaluate once on test — or relabel numbers as "empirical max test coverage at risk ≤R." Cheap-ish rerun or relabel.

### 6. The table path makes an extra OCR call (docTR)
1. The table witness runs docTR (an OCR model) on the crop, so "no extra model call" isn't literally true for tables.
2. **Known** — we always called it a docTR witness; the wording was loose.
3. **Yes (wording) + measure its cost.**
4. Accuracy of the headline claim. If we don't, it's a factual error a reviewer will flag.
5. **Current:** "no extra model call." **Suggested:** "no extra **generative** LLM/VLM call; optional lightweight **OCR** witness" + report docTR latency. Doc fix + small measurement. (Our structure-only 0.77 vs +witness 0.88 ladder stays.)

### 7. S1 has filing-level leakage
1. S1 is split by page, but pages from the same filing appear in both train and test — so the model may be memorizing filings, not generalizing.
2. **New catch** — we did not flag this.
3. **Yes.**
4. 0.960 doesn't prove cross-filing generalization. If we don't, the S1 number is inflated.
5. **Resolved (ran it):** with a proper **filing-grouped split** (no documents shared across train/test) the AUROC is **0.963** (≈ prior 0.960) — the result holds cross-filing, nothing was clubbed. Report **0.963** as the clean cross-filing number.

### 8. Signal is largely driven by the empty-rate prior
1. A static per-field "how often is this field empty" prior carries most of the Signal signal; much of the score isn't item-specific document evidence.
2. **Known — we found this ourselves** (drop-one).
3. **Yes — expose it + add baselines.**
4. It's a real, useful production finding; hiding it would be the dishonest move. If we don't, a reviewer discovers it and distrusts everything.
5. **Current (verified):** full **0.957** → without `gt_empty_rate` **0.654** (it carries ~0.30 of the AUROC). **Suggested:** add baselines (empty-only, prior-only, presence-only, 6-evidence-only, full) + report non-empty-only performance. (My quick pooled recompute today mis-read the features — failed reconciliation — so these baselines need a **correct cheap rerun** via the drop-one harness; the 0.957→0.654 fact is solid.)

### 9. Drop-one ablation is a surrogate model
1. The ablation trains a fresh pooled model, not the actual deployed per-domain models.
2. **Known.**
3. **Yes — relabel (or rerun deployed).**
4. It shows feature importance of a *surrogate*, not proof the deployed model behaves identically. If we don't, the equivalence claim is unsupported.
5. **Current:** called a faithful ablation (reconcile rule "AUROC>0.90"). **Suggested:** call it a "surrogate-model ablation," and reconcile the stale "not-faithful" JSON. Doc fix.

### 10. Placebo control is weak
1. We shuffle signals globally; that doesn't test whether the model leans on field identity, and the RD placebo is sensitive to tied zeros.
2. **Our method.**
3. **Yes (after #1 tie fix).**
4. The placebo doesn't rule out the field-identity shortcut. If we don't, "not chance" is unproven.
5. **Current:** global permutation. **Suggested:** permute *within field+domain*, run on the headline metric. Cheap rerun.

### 11. ParseBench annotation is thin (6 bad tables, single session)
1. The ParseBench labels were made in one pass with only 6 "bad" tables and no second annotator.
2. **Known** — we knew it's small.
3. **Yes — scope honestly.**
4. 6 tables can't anchor a "frontier"; and we shouldn't imply a rigorous labeling process. If we don't, it's over-claiming.
5. **Current:** ParseBench vision AUROC 0.912 presented as a result. **Suggested:** use **RD** for the tables frontier, keep ParseBench as supporting examples; say "zero false accepts **observed**," not "never." (ROCKET full-set run will grow the table error population.) Doc + optional 2nd annotation.

### 12. The 0/31 "not fundamentally undetectable" adjudication is single-reviewer
1. The claim that 0 of 31 hard cases are truly ambiguous came from one informal review, not a blinded two-annotator process.
2. **Known** — it was exploratory.
3. **Yes — scope or support it.**
4. Single-reviewer isn't evidence for a strong claim. If we don't, "fundamentally undetectable" (which we're dropping anyway) is unsupported.
5. **Current:** stated as a finding. **Suggested:** label it "exploratory single-reviewer inspection," or commit an anonymized manifest. Doc.

### 13. Numbers don't reconcile across files
1. Different docs/JSONs show different values for the same thing (RD 460 vs 287 tables; bad-catch 0.899 vs 0.835; sufficiency DROP in md but KEEP in json; etc.).
2. **Partly known** (e.g., we DECIDED sufficiency=DROP; the KEEP json is stale).
3. **Yes.**
4. Internal inconsistency is the fastest way to lose a reviewer. If we don't, the paper looks unreliable.
5. **Current:** scattered, some stale. **Suggested:** one machine-readable results registry; generate all tables from it; delete stale text. Bookkeeping (medium).

### 14. Weaker results are de-emphasized
1. The summary leans on the strong numbers and under-reports the weak ones (NDA ~0.53, FCC all-fields ~0.825 vs scalar-only 0.897, OmniDoc failing, cleanup hurting Charities).
2. **Known** — we knew NDA was thin and OmniDoc dropped.
3. **Yes — report all.**
4. Selective reporting is a rejection reason. If we don't, it reads as hiding failures.
5. **Current:** headlines = the strong subset. **Suggested:** report every domain + a scope table; treat exclusions as sensitivity analyses. Doc.

### 15. "Distribution-shift robustness" is really cross-domain
1. We trained a new model per dataset and called it shift-robustness; that's just evaluating on different datasets.
2. **Our naming.**
3. **Yes — rename.**
4. A real shift test freezes the model and changes vendor/template/time. If we don't, the term is wrong.
5. **Current:** "shift robustness." **Suggested:** "cross-domain evaluation." Doc.

### 16. Error definitions differ across the three legs
1. Each leg uses a different "correct/wrong" matcher and population rule, and the method text describes a two-classifier decision while some numbers come from a single model's probability.
2. **Partly known.**
3. **Yes.**
4. Inconsistent definitions make results incomparable. If we don't, the method section contradicts the results.
5. **Current:** implicit, inconsistent. **Suggested:** one per-dataset spec table (unit, matcher, missing-value rule, population, score, decision, threshold source); make method match config; test or drop the document-level conjunction claim. Doc + small.

### 17. Repo isn't reproducible/anonymous
1. Hard-coded personal paths, private repo dependencies, real names, internal product names.
2. **Known** — it's our internal repo.
3. **Yes — before any anonymous submission.**
4. NAACL submission is double-blind + should be reproducible. If we don't, we can't link the repo (or we deanonymize ourselves).
5. **Current:** internal paths/names throughout. **Suggested:** CLI args/config, lockfile, scrub names/paths, a small synthetic fixture; don't link the repo unless scrubbed. Medium.

### 18. Competitor comparisons aren't like-for-like
1. The Jin and ConfBench comparisons use different extractors/fields/base-rates, so they can't prove we're better.
2. **Known.**
3. **Yes — soften.**
4. Apples-to-oranges parity claims get challenged. If we don't, the comparison backfires.
5. **Current:** implied parity/edge. **Suggested:** present as contextual reference points only; no parity/superiority claims. Doc.

### Code-quality concerns (bundle)
Plausible silent-failure paths (proba→final_score fallback, NaN→bool, inverted bool, 0.0-trust dropped by truthiness, stale report generators). **Do:** convert to assertions + tests while regenerating. Cheap, worth it.

---

## Part B — "detectability frontier": keep it, reframed (not his, not ours — synthesize)
(Full mapping of the colleague's 10 requirements is in the chat; summary:)
- A median-score cutoff isn't a real frontier (he's right; our #4 sensitivity proves it).
- But an **evidence-relative frontier** — detectability shrinks as evidence grows (structure → +OCR geometry → +independent witness → generative judge → human), reported vs **cost** — is defensible AND we **already have ~70%** of it (tables ladder 0.77→0.88; the oracle decomposition).
- Of his 10 "must-haves": 5 we have, 4 are cheap (formalize regimes, calibration freeze, AUROC/bootstrap fix, cost numbers + controlled corruptions), 1 (blind 2-annotator) is human but scopable to the few-dozen residual cases.
- **Recommendation:** keep the frontier as the **"Evidence-Relative Detectability Frontier"** — preserves the novelty, drops the indefensible median definition, satisfies the rigor. Tables frontier must use **RD**, not 6 ParseBench tables.

## What moves a score vs what's doc-only
- **Score changes (ran today):** #1 negligible (+0.002–0.004, *higher*), #3 FATURA end-to-end **0.952** (from 0.994 located), #4 frontier becomes a sensitivity range.
- **Score changes (need a rerun — tell me to run):** #7 S1 filing re-split, #5 calibration-frozen coverage, #8 extra baselines, #2 wider CIs, #10 within-field placebo.
- **Doc-only (no score change):** #6, #9, #11, #12, #13, #14, #15, #16, #18.
