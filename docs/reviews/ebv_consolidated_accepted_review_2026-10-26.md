# Consolidated Accepted Review of the EBV Repository

**Date:** 2026-10-26  
**Target:** NAACL 2027 Industry Track  
**Combined from:** `ebv_paper_code_review_naacl_industry.md` and `repo_rereview_2026-10-26.md`

## Verdict

The repository contains enough useful work for an Industry Track paper, but the current headline claims are not submission-safe. The acceptable paper is an honest deployment-lessons paper about what inexpensive evidence can detect, which priors and shortcuts the verifiers depend on, and where an extra OCR or model call becomes necessary.

**Recommendation: proceed only after the Tier 1 corrections below.** Do not submit the current “detectability frontier” and FATURA 0.994 story unchanged.

The strongest defensible thesis is:

> We study lightweight verification of document-extraction outputs across structured fields, variable-layout fields, and tables. We quantify what cheap document-derived evidence and static priors catch, identify their operational blind spots and domain boundaries, and measure the incremental value of an independent OCR witness—without another generative-model call.

## Findings accepted as confirmed blockers

### 1. The shared AUROC implementation is wrong for tied scores

`experiments/indirect/scripts/lib_frontier.py::auroc` assigns sequential ranks rather than average ranks to ties. Results can depend on input ordering, and constant or heavily tied channels can receive invalid AUROC values. This affects indirect per-channel results, ablations, placebo results, and reconciliation checks.

Required action:

- Replace it with `sklearn.metrics.roc_auc_score` or a tested average-rank implementation.
- Do not automatically flip channel direction after inspecting results; specify each direction in advance.
- Add unit tests containing all-equal scores, binary scores with many ties, reversed scores, and a comparison with scikit-learn.
- Regenerate every artifact that imports `lib_frontier.py`.

### 2. The grouped bootstrap implementation is invalid

The bootstrap samples document or table identifiers with replacement and then selects rows using `isin(pick)`. This discards duplicate draws, so it is not a cluster bootstrap.

Required action:

- Concatenate the rows belonging to every sampled group while preserving repeated groups.
- Regenerate all confidence intervals.
- Add tests showing that a group sampled multiple times appears multiple times.
- Compute CIs for headline AUROC and deployed operating-point metrics, not only frontier quantities.

### 3. Structured AUROC excludes unlocated outputs

FATURA and VRDU AUROC calculations drop rows with `wv_score=None`. Those rows remain in the coverage denominator as never accepted, but they do not affect AUROC. This makes the structured AUROC conditional on successful value localization and substantially weakens the 0.994 FATURA headline.

The flat FATURA coverage values across 5%, 10%, and 20% risk are consistent with localization—not the risk constraint—setting the ceiling.

Required action:

- Report both conditional AUROC on located items and end-to-end AUROC on all eligible items.
- For an end-to-end score, assign unlocated outputs the lowest trust score or define a documented deterministic score.
- Always report `n_total`, `n_scored`, and localization rate.
- Add a simple value-present-in-OCR baseline.
- Recompute FATURA and VRDU headlines before deciding which result belongs in the abstract.

Until this is fixed, **FATURA 0.994 must not be the headline**.

### 4. The frontier definition does not establish undetectability

The current “confidently wrong” frontier is an accepted error whose fused score is at least as clean as the median correct output. The median is an arbitrary post-hoc cutoff. Changing it changes the claimed frontier.

The repository also says these cases are flagged as `INSUFFICIENT`, but the frontier definition requires that they were accepted. Those statements cannot both be true.

The source review finding that 0/31 cases are fundamentally ambiguous further shows that the experiment measures verifier/channel limitations rather than a fundamental information limit.

Required action:

- Rename the construct **operational blind-spot rate** or **evidence-limited verification frontier**.
- Primary measure: escaped errors at a threshold fixed on a calibration set.
- Diagnostic sensitivity: all escaped errors and the subset above the 25th, 50th, and 75th percentiles of correct scores.
- Report the original fixed-false-review channel oracle as a separate diagnostic, including the union false-review rate.
- Delete the claim that accepted frontier errors were flagged as insufficient.
- Reserve “fundamentally undetectable” for human-adjudicated source-ambiguous cases.

### 5. Coverage at fixed risk is optimized on the evaluation labels

Signal, structured, ParseBench, sufficiency, and indirect channel scripts select thresholds or maximum coverage using the same labels on which results are reported. These are oracle empirical test curves, not deployable calibrated coverage.

Required action:

- Use train/calibration/test separation and choose thresholds only on calibration.
- Evaluate the frozen threshold once on test.
- If rerunning is impossible, label existing results exactly as **empirical maximum test coverage at observed risk ≤R**.
- Do not describe those values as guaranteed or safely calibrated automation.

### 6. The table path uses an additional OCR inference

The table experiments run docTR directly on crops. Therefore “without extra language- or vision-model calls” and “model-free table verification” are inaccurate.

Use this claim instead:

> EBV does not require another generative LLM or VLM call; its optional table witness incurs one lightweight OCR inference.

The strongest table result is the cost ladder on a consistent RD subset:

| Configuration | Additional inference | Approximate AUROC |
|---|---:|---:|
| HTML-internal structural evidence | None | 0.77 |
| Structure plus independent docTR witness | OCR inference | 0.88 |

Measure docTR latency, hardware, memory, and throughput. Do not combine the 460-table RD operating-point result with the 287-table signal-ablation result without clearly distinguishing their populations.

### 7. S1 has filing-level leakage

The S1 split is page-level while pages from the same filing occur in both train and test. Consequently the 0.960 AUROC does not establish cross-filing generalization.

Required action:

- Re-split by filing or source document.
- Retrain and recompute S1 metrics.
- Report the current result only as within-filing/page-level performance if retained.

### 8. Signal performance is heavily driven by a static field prior

Dropping `gt_empty_rate` reduces the surrogate pooled AUROC from approximately 0.957 to 0.654. Most Signal errors are empty extractor outputs. This means much of the result comes from a per-field empty prior or field-identity proxy rather than item-specific document evidence.

This is a valid and useful production finding, but the paper must expose it.

Required baselines:

- Field identity or field correctness prior.
- `is_empty` alone.
- `gt_empty_rate` alone.
- Field prior plus `is_empty`.
- Value-present-in-source/OCR rule.
- Six document-derived signals without static priors.
- Full verifier.
- Within-field permutation rather than global permutation.

Also report Signal performance on non-empty predictions separately from extractor-empty failures.

### 9. The Signal drop-one experiment is a surrogate ablation

The script trains a new pooled Gradient Boosting model under grouped cross-validation rather than ablating the deployed per-domain production models. Its reconciliation rule accepts any AUROC above 0.90, which is insufficient evidence of behavioral equivalence.

Required action:

- Call it a **surrogate-model ablation**, or rerun the production training pipeline with each feature removed.
- If retaining the surrogate, compare AUROC, score correlation, and decision agreement with the deployed models.
- Reconcile the markdown claim with the JSON artifact that labels an earlier version “not-faithful.”

### 10. The placebo control is insufficient and partly artifactual

Global permutation does not test whether Signal relies on field identity or prevalence. The RD placebo is sensitive to tied zero scores and strict inequality, and the reported collapse to zero is not a reliable chance baseline.

Required action:

- Fix AUROC and threshold tie handling first.
- Permute Signal evidence within each field and domain.
- Run the placebo on the headline metric, not only an auxiliary oracle measure.
- Preserve missingness patterns during permutation.
- Report the expected chance behavior analytically or by simulation with confidence intervals.

### 11. ParseBench annotation is insufficiently documented

The labels were produced in one session; many examples are marked borderline; only six tables are bad. There is no committed second-annotator record, blinding protocol, rubric, agreement score, or adjudication history.

The repository does not establish who or what produced the labels. Do not assert an AI labeler without evidence; instead disclose the actual process accurately.

Required action:

- Obtain a second independent human annotation.
- Blind annotators to trust scores and reason codes.
- Use a written rubric.
- Report raw agreement, Cohen’s kappa, and adjudicated labels.
- Report exact/binomial uncertainty.
- Say “zero false accepts observed in this sample,” not “never wrongly accepts.”
- Correct or relocate the misfiled `vlm_labels.json` artifact.

### 12. The 0/31 adjudication claim is not adequately supported

The repository contains RD crops but not a complete auditable annotation record for the eight Signal cases, and VRDU frontier cases are not included. Blinding and inter-annotator agreement are not documented.

Required action:

- Commit an anonymized manifest with case ID, source-observability label, annotators, disagreement, and adjudicated result.
- Scope the claim to the modes actually reviewed.
- Otherwise describe the 0/31 result as exploratory single-reviewer inspection or remove it.

### 13. Several headline populations and numbers do not reconcile

Accepted inconsistencies requiring resolution include:

- RD headline results use different populations: approximately 460 tables for one operating-point result and 287 for the signal ablation.
- RD bad-catch is reported as both 0.899 and 0.835.
- ParseBench example idx29 has inconsistent trust values.
- Sufficiency is DROPPED in markdown but KEEP in JSON.
- Signal ablation has conflicting “reconciled” and “not-faithful” artifacts.
- FATURA frontier is described as both a nonzero in-place wrong-value tail and approximately zero.
- Some confidence-interval values use inconsistent units or rounding.

Required action:

- Create a single machine-readable canonical results registry with dataset, population, configuration, label rule, sample count, metric, and source artifact.
- Generate all README and paper tables from that registry.
- Delete or clearly mark superseded documents.
- Prevent report-generation scripts from overwriting corrected findings with stale text.

### 14. Results are selectively presented

The top-level summary omits or de-emphasizes important negative or weaker results:

- NDA AUROC around 0.53.
- FCC all-fields AUROC around 0.825 while the headline uses scalar-only 0.897.
- Cleanup improves FCC but reduces Charities performance.
- OmniDoc table verification fails badly.
- VRDU uncalibrated GT-ROI ranks above the production score while having a worse deployed operating point.
- S1’s low base error makes some coverage targets trivial.

Required action:

- Report every evaluated domain in the main results or an explicit scope table.
- Clearly distinguish scalar-only from all-field populations.
- Include OmniDoc as a negative domain-boundary result.
- Report accept-all risk alongside coverage-at-risk.
- Treat excluded fields and subsets as sensitivity analyses, not co-equal headlines.

### 15. Cross-dataset retraining is not distribution-shift robustness

Training a separate model on every new dataset with different fields, labels, and base rates does not demonstrate graceful degradation under shift.

Use the term **cross-domain evaluation**, not shift robustness. A genuine shift experiment must freeze the verifier and evaluate it on a changed vendor, template, time slice, or extractor.

### 16. Error definitions and system behavior are inconsistent across legs

The three legs use different correctness matchers and population rules. “Present field” does not have one consistent definition. The paper also describes a two-classifier agreement decision while some headline AUROC values come from a single model’s probability. Empty-prior behavior is described as active even where the logs show it never fires.

Required action:

- Add a table specifying, for every dataset, the unit, correctness matcher, missing-value treatment, population filter, score, deployed decision, and threshold source.
- Make the method text match the actual headline configuration.
- Separate the continuous ranking score from the deployed binary decision.
- Test or remove the unified document-level conjunction claim; it is currently formulated but not evaluated across the full system.

### 17. The repository is not independently reproducible or anonymous

The repository contains hard-coded personal paths, private cross-repository dependencies, ignored decision logs, internal product/repository names, and organization-identifying material. The README refers to a data README that is missing or not available at the claimed location.

Required action:

- Replace absolute paths with CLI arguments or configuration.
- Add environment lockfiles.
- Add a small synthetic fixture and one validation command.
- State which results require private code or licensed data.
- Add metric and pipeline unit tests.
- Scrub names, personal paths, internal links, and organizational identifiers before attaching supplementary material.
- If the code cannot be anonymized and made coherent in time, do not link the repository in the anonymous submission.

### 18. Competitor comparisons are not like-for-like

The Jin and ConfBench comparisons use different extractors, fields, populations, correctness rules, base error rates, and model access. They are useful context but do not support parity or superiority claims.

Required action:

- Present them as contextual reference points.
- Do not claim parity with Jin or a direct win over ConfBench.
- Verify all recent citations and accurately characterize their inference costs.

## Additional code-quality concerns to repair

The second review identifies several plausible silent-failure paths that should be tested before regenerating results:

- Exception-swallowing fallback from probability to `final_score`.
- Boolean conversion of NaN values.
- Possible inverted boolean signal encoding.
- Dropping a valid trust score of `0.0` through truthiness checks.
- Incomplete tuned runs.
- Report generators that can recreate stale claims.

These should be converted into explicit assertions and tests. Do not silently substitute scores or labels.

## Results that remain useful after reframing

Subject to corrected computation, these are the strongest pieces of the paper:

1. **Independent OCR helps table verification.** On a consistent RD subset, adding docTR improves AUROC by roughly 0.11 over HTML-internal evidence.
2. **Static field priors are operationally powerful.** The empty-rate prior carries substantial unique Signal information, revealing a real production dependency.
3. **The hard residual is plausible but wrong.** Cross-field copies, wrong values already present elsewhere in the document, and structurally plausible table scrambling are recurring difficult families.
4. **Domain boundaries are real.** OmniDoc, NDA, and Charities show that inexpensive verification is not uniformly reliable.
5. **A zero-generative-call path exists.** Structured fields, unstructured text signals, and structure-only tables can be scored without another generative LLM/VLM call, with an optional OCR witness for higher table quality.

## Claims to avoid

- “FATURA AUROC 0.994” as the primary end-to-end result.
- “No additional vision-model call” for the docTR table path.
- “Never wrongly accepts.”
- “Fundamentally undetectable errors.”
- “All experiments complete and reconciled.”
- “Graceful degradation under distribution shift.”
- “Parity with Jin et al.”
- A direct superiority claim over ConfBench.
- “Production-safe coverage at 5% risk” when thresholds were selected on test.
- “The system flags frontier errors as insufficient” when those errors were accepted.

## Tier 1 actions before submission

1. Fix AUROC ties, group bootstrap multiplicity, direction handling, and threshold ties; add tests.
2. Recompute structured AUROC on all rows and report localization coverage.
3. Re-split S1 by filing and rerun it.
4. Introduce a calibration split or relabel coverage numbers as oracle empirical test coverage.
5. Replace “no extra model call” with “no extra generative-model call”; measure docTR cost.
6. Replace the detectability-frontier claim with operational blind spots and sensitivity bins.
7. Add field-prior, empty-only, presence-only, evidence-only, and full Signal baselines.
8. Reconcile all markdown/JSON/population inconsistencies through one generated results registry.
9. Report NDA, FCC all-fields, OmniDoc, and all exclusions.
10. Correct the annotation claims or complete blinded second annotation.
11. Scrub or withhold the non-anonymous repository.
12. Update the paper from “ARR long paper” to the six-page NAACL Industry Track format and add the mandatory Limitations section.

## Recommended six-page paper

### Suggested title

**What Cheap Evidence Buys: Verifying Document Extraction Without Another Generative-Model Call**

### Structure

1. **Introduction** — production verification problem, human-review cost, and contribution.
2. **System** — shared accept/route interface, three modes, and inference-cost ladder.
3. **Evaluation** — datasets, population definitions, calibration/test protocol, annotation, baselines, and metrics.
4. **Results** — corrected domain-specific results; no pooled headline.
5. **Deployment lessons** — priors versus document evidence, independent OCR value, difficult error families, and domain failures.
6. **Limitations and conclusion** — small labeled table sets, private dependencies, absence of an LLM-judge baseline, and no genuine frozen-model shift test.

### What to headline after correction

- The structure-only versus OCR-witness RD comparison on the same population, with latency.
- Domain-specific Signal results after fixing the S1 split, with field-prior baselines.
- Corrected all-row VRDU performance with localization rate and confidence intervals.
- The plausible-but-wrong hard tail.
- OmniDoc, NDA, and Charities as scope boundaries rather than hidden failures.

Use FATURA, ParseBench, excluded-field variants, and median-score frontier bins as controlled or sensitivity analyses.

## Final decision

The combined evidence supports a paper, but not the paper currently advertised by the README. The credible Industry Track contribution is a transparent account of **what cheap verification evidence buys, how much performance comes from static priors, when an independent OCR witness is worth its cost, and which realistic errors still escape**.

If the Tier 1 fixes cannot be completed and the draft cannot be rewritten around those corrected findings, the work should target a later venue rather than submit inflated or internally inconsistent claims.
