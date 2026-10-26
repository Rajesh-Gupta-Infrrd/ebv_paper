# Evidence-Based Verification for Document AI

## Research Specification v3 (refined)

**Status:** Refined draft for team review · **Date:** 2026-09-28
**Supersedes:** `evidence_based_document_ai_verification_research_spec_v2.md` (merged)
**Source systems:** Structured-field NTP (ROI), Unstructured-field NTP (Signal), Table Trust Scoring

> **What changed from v2 → v3 (summary).** This version keeps the strong core of v2 and tightens scope after a full design review. Headline changes:
>
> - **Framing locked:** one system with **three modes** (structured field / unstructured field / table), unified by a shared formulation, output, and evaluation — *not* by a shared combiner. "NTP" is the application; the contribution is the evidence formulation + detectability analysis.
> - **Constructs:** detectability (with the frontier) and complementarity are **core**; **sufficiency is optional/pilot-gated** (it is largely a per-item re-mix of detectability and must earn its place).
> - **Hypotheses:** H1(b) softened to a **cost-trade-off** claim (not "match the LLM"); H3 reframed as a **supporting** (known) result, not novelty; **H4 and H6 optional**; **H5 (frontier) is the novelty pillar**.
> - **Evaluation:** oracle decomposition **promoted to a headline metric**; **per-channel continuous logging** made a rule; placebo tied to every headline number; **conformal risk dropped** (binomial bound kept); incident-level capture optional.
> - **Experiments:** **E3c and E7 removed**; E3a downgraded to an optional gap-filler; E4b/E5/E-cost optional/pilot-gated; E6 partly reusable.
> - **Failure families** grouped from ~~15 flat to **~~7 field + ~5 table** buckets for statistical density; "partial/truncated value" added.
> - **Scope:** semi-structured docs fold into the **unstructured** mode; **checkboxes/signatures out of scope** (coverage gap).
> - **Reproducibility:** private data/code stays private; **public benchmarks now cover all three modes** — tables (RD-TableBench), structured fields (FATURA + FARA), unstructured fields (RealKIE, optionally DocILE) — each a first-class result; method described in full (as normal).
> - **Structure:** paper structure finalized to the standard NAACL skeleton (abstract + mandatory Limitations + advisable Ethics); the end-to-end solution flow added up front (§1.5); the experiments table now shows the work type (re-score / annotation / new / rerun / witness).
> - **Trimmed:** related-work citation list deferred to writing; the risk register refined (Table-Trust "overfit" row removed — it was not tuned to the dataset — and trimmed to core research risks); ablations cut to the feasible set (dependency/provenance, native-vs-common-fusion, and typed-generic experiments dropped).

---

## 0. TL;DR

- **What we mean by verification.** At inference time we decide whether an extraction can be trusted **without any additional LLM call**. The extractor runs once. Verification uses only non-LLM evidence already in the document: OCR, layout, structure, learned priors, lightweight signals.
- **We have three zero-extra-LLM verifiers, presented as three modes of one system:**
  - **Structured field mode** (template docs) — ROI/location evidence.
  - **Unstructured field mode** (free-form docs; semi-structured folds in here) — text-grounding signals.
  - **Table mode** — structure + independent-witness evidence.
- **Thesis.** Every output leaves traces in its source document. Different evidence channels expose different failure mechanisms. How much we can safely automate depends on which evidence is available, how complementary the channels are, and which failure types they can detect at all.
- **Headline claim.** With zero extra LLM calls, document evidence should beat equal-cost baselines and sit on a better cost/risk/coverage trade-off than LLM-based verification. **Some errors are undetectable from any available evidence — the system should say so instead of calling them "verified."**
- **NTP is the application, not the contribution.** The contributions are: the formulation, one shared evaluation protocol, the map of which failure families each channel can detect, the complementarity analysis, and the **detectability frontier**.

---

## 1. Framing

### 1.1 Claims we can and cannot make


| Claim                                                  | OK?                                                                                         |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| "Verification **without inference-time ground truth**" | ✅ GT is used only offline (ROI blueprints, classifier training, threshold tuning, grading). |
| "**Zero additional LLM calls** at inference"           | ✅ The defining constraint of the method class.                                              |
| "GT-free verification / GT-free accuracy"              | ❌ False. ROI is built from golden data; Signal classifiers are trained on GT.               |
| "We determine whether the LLM is correct"              | ❌ We measure the evidence for/against an output, which is not the same thing.               |


### 1.2 Correctness ≠ verifiability

A verifier cannot answer "is this correct?" It answers "**what observable evidence supports or contradicts it?**" Every channel has blind spots (e.g. a shared OCR misread that both the extractor and the source-grounding check inherit).

### 1.3 Research question

> Given a Document AI output (a field or a table), and using **zero additional LLM calls**, what observable document evidence could reveal that the output is wrong? Which failure mechanisms can each evidence channel expose, how complementary are the channels, and how much automation is safe at a bounded residual error compared with LLM-based verification?

**Working title (LOCKED):** "**The Detectability Frontier of Document Extraction Errors: Verification Across Fields and Tables Without Extra Model Calls**"
- *Fallback A:* "…: Source-Evidence Detection Across Fields and Tables" (drops the cost clause; cleaner but hides our differentiator).
- *Fallback B (question form):* "Which Document Extraction Errors Leave Detectable Traces? Verification Across Fields and Tables Without Extra Model Calls".
- *"Detectability" (not "floor"):* we **measure** what the evidence catches vs. misses (a map + an honest residual); we do **not** claim proven impossibility. The genuinely-uncatchable cases are reported as an adjudicated *source-ambiguous* subset, not asserted as a universal floor.
- **Precise meaning of "Without Extra Model Calls" (hold this wording in the paper):** verification adds **no extra LLM/VLM inference**. Structural signals are computed directly from the extraction output (model-free); the optional independent-OCR witness is **reused from the existing parse pipeline** (or, on datasets without shipped OCR, a single lightweight OCR pass) — **never a generative/vision-model call.** *(Note: docTR etc. are OCR libraries that run neural models, so the claim rests on **reuse**, not on "OCR isn't a model.")*
- *Note:* the title is framing only — the formulation, systems, experiments, and findings are identical regardless of which is chosen; swapping is a one-line change.

### 1.4 System framing — one system, three modes

The three verifiers are **modes of one system**, unified by:

1. **One formulation** — evidence channels → decision.
2. **One output** — `CORROBORATED / CONTRADICTED / CONFLICTED / INSUFFICIENT` → accept / review.
3. **One evaluation** — the same error definitions, metrics, and analyses.

A lightweight **router** selects the mode from the input type. The modes differ only in *which channels* they use, because different inputs expose different evidence. They are **not** required to share one combiner (fusion); each mode keeps its own tuned combiner (§6.5).

### 1.5 The approach end-to-end (how we frame the solution)

The solution has two layers: a **runtime** decision path and an **offline evaluation** path. Ground truth appears only in the second.

**Layer A — Runtime (a real document; no ground truth):**

```
1. INPUT     an AI output (field or table) + the source document
2. ROUTER    pick the mode by input type (structured field / unstructured field / table)
3. CHANNELS  run the evidence channels available for that mode
4. SCORES    each channel emits support / contradict / neutral + a continuous score (logged)
5. FUSION    the mode's tuned combiner turns the channel scores into one trust score
6. STATE     CORROBORATED / CONTRADICTED / CONFLICTED / INSUFFICIENT
7. DECISION  accept (NTP) / send to review   (INSUFFICIENT may escalate even if nothing contradicts)
```

**Layer B — Offline evaluation (ground truth lives only here):**

```
1. GT labels each output correct/wrong (§8.1) — the label the verifier should predict
2. Reuse the logged channel scores + annotate real errors by family
3. Compute: performance (H1), detectability map (H2), complementarity (H3),
   the oracle decomposition / frontier (H5), robustness (shift), validity (placebo)
```

**The rule that ties them together:** the verifier (Layer A) never sees ground truth; ground truth (Layer B) only grades it and measures what is fundamentally undetectable.

---

## 2. Current state of the source systems

### 2.1 Structured-field mode (ROI)

- Single LLM extracts fields; each value is mapped to OCR boxes and scored against a per-field ROI (percentile union box, IQR outlier filtering): `overlap_w·overlap + center_w·center + iou_w·IoU ≥ threshold`. Weights/threshold grid-searched per field. A document is accepted only if every field passes.
- **Known limits:** template-dependent; cannot handle checkboxes/signatures/stamps; takes the first match for duplicate values; **cannot detect a wrong value in the right location.**
- **For this paper:** ROI becomes **one channel family (historical prior + weak source-grounding)**, not a standalone algorithm. Reuse the logged overlap/center/IoU components (expose them only if a run saved just pass/fail). Duplicate handling (`applicable=false` / best-occurrence) is an **optional** improvement.

### 2.2 Unstructured-field mode (Signal)

- Non-LLM signals (`format_valid`, `keyword_context`, `source_context`, `value_in_text`, `label_value_distance`, `partial_extraction`) feed per-doc-type tree classifiers (RF/GBM/XGB/LGBM). Optional 3-tier router → NTP / LLM_REVIEW / HUMAN_REVIEW.
- **Semi-structured docs (paystubs, bank/credit statements) fold into this mode.**
- **For this paper:** reuse the per-signal logs (already available); the tree classifier is this mode's combiner. Splits are **already document-disjoint** (§8.2) — reusable. Rewriting field-specific patches as typed mechanisms (`type_incompatibility`, `source_absence`, `label_value_mismatch`, `cross_field_copy`, `value_position_inconsistency`) is **optional** (report dropped patches in an ablation).

### 2.3 Table mode (Table Trust)

- Inputs: table HTML (MinerU/GLM/Parse), optional crop, optional **independent** OCR witness (docTR/native — same-engine block text excluded). Core signals: crop/boundary (20, off by default), geometry/topology (25), structural plausibility (25), content conservation (25). Post-core: concat-merge, missing-content, token layout, reading order, structural defect detectors. Accept rule: score ≥ 85.
- **Already aligned with this paper:** the witness-independence rule (= complementarity) and the failure-family hints (= detectability). **The independent docTR witness is already built in** (no extra work to obtain the independent channel for tables).
- **For this paper:** per-signal exposure and the docTR witness are **already in place** — only **freeze the version + threshold**, and label table errors per §8.1 (annotation).

### 2.4 Where current evidence sits in the taxonomy


| System (mode)         | Output-internal      | Source-grounding      | Independent witness  | Prior                   | Relational |
| --------------------- | -------------------- | --------------------- | -------------------- | ----------------------- | ---------- |
| Structured (ROI)      | —                    | weak (OCR box match)  | —                    | ✓ ROI                   | —          |
| Unstructured (Signal) | ✓ format             | ✓ value/label/context | —                    | (learned by classifier) | —          |
| Table (Trust)         | ✓ topology/structure | ✓ crop bands/valleys  | ✓ docTR conservation | —                       | —          |


**Gaps:** the field modes have no *independent* witness channel (their source-grounding likely uses the same OCR the extractor saw) — an **optional** addition (§6.4). No mode has a **relational** channel; building one is **out of scope** (business-logic consistency over hundreds of domain constraints), noted only as future work.

---

## 3. Research object

For each prediction unit:


| Symbol     | Meaning                                                     |
| ---------- | ----------------------------------------------------------- |
| `x`        | source document/region                                      |
| `y`        | primary Document AI output                                  |
| `c`        | latent correctness of `y` (known only offline, for grading) |
| `E`        | evidence observations, one per channel                      |
| `A`        | channel availability/applicability                          |
| `F`        | failure family (annotated on errors)                        |
| `R`        | estimated residual error risk                               |
| `decision` | accept / review                                             |


**The one rule:** `decision = f(E, A)` — the verifier uses only evidence and availability, **never `c`**. Ground truth (`c`) is used *only offline* to grade the verifier and to measure the detectability frontier.

**Records.** Every experiment logs a per-output record and, within it, a **per-channel record with a continuous score** (not just a final label). Continuous per-channel logging is mandatory — it is what makes the constructs computable by re-scoring rather than re-running. The record format itself is bookkeeping, **not** a contribution.

---

## 4. Evidence states and taxonomy

### 4.1 Four evidence states


| State          | Meaning                                                  | Default policy                          |
| -------------- | -------------------------------------------------------- | --------------------------------------- |
| `CORROBORATED` | ≥1 material channel supports; no material contradiction. | Accept                                  |
| `CONTRADICTED` | Material contradiction; no material support.             | Review / re-extract                     |
| `CONFLICTED`   | Material support and contradiction both present.         | Review (log)                            |
| `INSUFFICIENT` | No applicable channel gives a material signal.           | Review, or accept against a risk budget |


Material thresholds are fit on the calibration split only. These are **evidence states, not correctness labels.**

### 4.2 Evidence taxonomy (channels)


| Level | Family              | V1 channels                                                                                          |
| ----- | ------------------- | ---------------------------------------------------------------------------------------------------- |
| L0    | Output-internal     | `format_valid`, HTML geometry/topology, structural plausibility                                      |
| L1    | Source grounding    | `value_in_text`, `keyword_context`, `source_context`, `label_value_distance`, crop bands/valleys     |
| L2    | Independent witness | docTR/native-OCR conservation (tables); **optional new:** independent OCR on the field region (§6.4) |
| L3    | Historical prior    | ROI blueprint, empty-field prior                                                                     |
| L4    | Relational          | **Not used — future work.** Cross-field constraints / table totals = business-logic consistency; out of scope here |
| —     | Cross-document      | **Out of scope**                                                                                     |


---

## 5. Core constructs

> Constructs are **offline measurements** that turn "our system works" into generalizable findings. They are the analysis lens, **not** the runtime control flow.

### 5.1 Detectability (core)

For a failure family *f* and channel *k*, at a fixed false-review rate (5% of correct outputs flagged):

```
Detection(f, k) = P(channel k gives a material contradiction | output wrong, family f)
```

Each error is *directly detectable / partially / indistinguishable* under the current evidence. Estimated on natural errors (primary) and, where natural examples are too few, on controlled corruptions (gap-filler). **The detectability frontier — errors no channel can catch — is the headline finding.**

### 5.2 Complementarity (core; replaces "independence")

On the primary extractor's errors, with `z_k = 1` if verifier *k* exposes the error, measure: pairwise overlap, **unique capture** (errors only *k* exposes), `MarginalUtility(j | S) = Capture(S ∪ {j}) − Capture(S)`, and `CostAdjustedUtility = MarginalUtility / Cost`. This tests whether a verifier that fails *differently* is worth more than a strong one that repeats the extractor's mistakes. (This is the general form of the Table-Trust witness-independence rule.)

### 5.3 Oracle observability ceiling + error decomposition (core; the frontier)

Each channel is set to its threshold at a **fixed 5% false-review rate** (mandatory — otherwise a loose channel trivially flags everything).

```
OracleCapture = |errors with ≥1 channel contradicting at its 5%-FRR threshold| / |all primary errors|
```

```
100% primary errors (excluding disputed/ambiguous GT; reported separately)
 ├── X% observable by ≥1 channel
 │     ├── Y% caught by the fused verifier
 │     └── (X−Y)% observable but missed   → modelling problem (fixable: improve fusion)
 └── (100−X)% observable by no channel     → detectability frontier (evidence problem)
```

This separates "the evidence couldn't see it" from "the fusion didn't use it." **Promoted to a headline metric.** Note: `OracleCapture` (X) is fusion-independent; the caught/missed split (Y) uses the mode's own combiner.

### 5.4 Evidence sufficiency (OPTIONAL — pilot-gated)

Per-item measure of how much of the plausible failure space the *available* channels can inspect:

```
S(o) = Σ_f w(t,f) · Detectable(f, A_applicable(o))
```

Distinguishes "low risk, high sufficiency" (checked and clean) from "low risk, low sufficiency" (couldn't check). **This is largely a per-item re-mix of detectability**; the only new information is per-item channel availability. **Include only if it demonstrably improves the risk-coverage trade-off over risk alone (H4).** Otherwise report the INSUFFICIENT-state rate as an honesty number and drop the estimator.

---

## 6. Modes, channels, and required changes

### 6.1 Testbed A — structured fields (ROI as one channel family)
Public leg: **FATURA** (50 templates × ~200 docs × 24 fields, synthetic invoices) + **FARA** (real US-gov forms). Internal: proprietary mortgage ROI docs.

### 6.2 Testbed B — unstructured/semi-structured fields (Signal channels)
Public leg: **RealKIE** (finance, variable-layout; + optional **DocILE**). Internal: proprietary mortgage unstructured docs.

### 6.3 Testbed C — tables (whole-table reliability + failure families; RD-TableBench held-out split + internal tables; target ≥200 errors)
Public leg: **RD-TableBench** (+ optional DocILE LIR / a second public table set).

### 6.4 System readiness — what's already done vs. remaining

Most instrumentation already exists: the source systems logged per-item detail during their own evaluations, so the **default is reuse existing logs and re-score — not re-run**. Status:

**Already satisfied (reuse as-is):**

- **Per-channel logs:** where existing runs saved each channel's continuous score per item, reuse directly. Re-score *only* where a system saved just the final label (verify per system).
- **Signal — disjoint splits:** already document-disjoint and held out (§8.2). Genuine and reusable.
- **Table Trust — instrumentation:** already exposes each core signal per item and already runs the independent docTR witness. Only step left: **pin (freeze) the version + threshold** used.
- **ROI — components:** reuse the logged overlap/center/IoU where present; expose them only if a run saved just pass/fail.

**Remaining (mostly annotation or optional — none are blockers to reuse):**

- **Error labelling (required — annotation, not instrumentation):** label field and table errors by family per §8.1 / §9.1. This is the main non-compute work (E3b).
- **Cost logging:** ensure `llm_calls` / tokens / latency are captured per arm (add if missing).
- **ROI duplicate handling (optional):** score every occurrence of a duplicate value and take the best; set `applicable=false` when a value occurs more than once. An improvement, not a blocker.
- **Signal typed mechanisms (optional):** rewrite field-specific patches as typed mechanisms (`type_incompatibility`, `source_absence`, `label_value_mismatch`, `cross_field_copy`, `value_position_inconsistency`); patches that don't generalise are dropped and reported in an ablation.
- **(OPTIONAL) L2 field witness — P1:** second OCR (docTR) on the field region, *offline on the test set*, compared to the prediction and logged. **Not a production component.** Needs stored page images; pilot-gated (keep if it adds catch, or cleanly shows it does not).

*(An L4 relational channel — cross-field sums, date ordering, table totals — is **out of scope**: it is business-logic checking, not extraction verification, and would require hundreds of domain constraints. Noted as future work only.)*

### 6.5 Fusion (the combiner)

Each mode keeps its **own tuned combiner** as primary (ROI weighted vote; Signal tree; Table-Trust weighted score) — do **not** replace them; the genuine tuned results stand. **Optional back-pocket comparison:** a single simple fusion (e.g. logistic regression) fit per mode on the logged channel scores, to (a) support the "it's the evidence, not the model" point and (b) neutralise any "not really one system" objection. Report the native combiners (incl. the tree model) alongside. The core constructs (§5.1–5.3, except the caught/missed split) are computed at the channel level and are **independent of the combiner choice.**

---

## 7. Hypotheses


| ID     | Hypothesis                                                                                                                                                                                                                                                              | Role                      | Status                                                                                             |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------- |
| **H1** | With zero extra LLM calls, evidence fusion (a) **beats equal-cost baselines** on coverage at fixed residual risk, and (b) sits on a **better cost/risk/coverage trade-off** than LLM-based verification (not necessarily higher coverage). Holds for fields and tables. | **Headline**              | Keep — part (b) is a *trade-off* claim, not "match the LLM"                                        |
| **H2** | Different evidence families expose statistically different failure families (detectability heatmap).                                                                                                                                                                    | **Main**                  | Keep                                                                                               |
| **H3** | A verifier's **unique capture** of the extractor's errors predicts its stack value better than its standalone accuracy.                                                                                                                                                 | Supporting                | Keep — a **known ensemble principle shown in a new setting**, not claimed as novelty               |
| **H4** | Conditioning acceptance on **risk + sufficiency** improves the risk-coverage trade-off under dropout/shift.                                                                                                                                                             | Secondary                 | **Optional** — include only if it beats risk alone                                                 |
| **H5** | A non-trivial share of real errors is **undetectable under available evidence**; flagging these blind spots reduces false claims of verification.                                                                                                                       | **Main — novelty pillar** | Keep — mandatory                                                                                   |
| **H6** | Source-grounded/witness channels (L0–L2) degrade less than priors (L3) under shift.                                                                                                                                                                                     | Analysis                  | **Optional** — frame around *what survives* (ROI failing on unseen templates is near-definitional) |


"Model confidence is imperfect" is not a hypothesis — it is a **baseline**.

---

## 8. Evaluation protocol (identical across modes)

### 8.1 Error definitions (frozen in Phase A) — defines `c`


| Testbed | Unit  | Error =                                                                                                   |
| ------- | ----- | --------------------------------------------------------------------------------------------------------- |
| A, B    | field | Normalised prediction ≠ normalised GT (existing per-type normalisers). **Empty vs empty = correct.**      |
| C       | table | **Primary:** TEDS(pred, GT) < τ, τ fixed before scoring (proposal 0.9). **Secondary:** any cell mismatch. |


Also report **document-level** results for A and B (a document is accepted only if all its fields are), because production routes whole documents.

> Note: §8.1 defines whether the **extraction** is correct (the label `c`). The **verifier's own error** — flag vs `c` — is measured separately by escaped errors / false reviews (§8.3).

### 8.2 Splits

- **Main:** document-disjoint; template/vendor-disjoint where IDs exist. **No random field-level splits.** (Confirmed: the source systems' test sets are document-disjoint and held out — reusable.)
- **Calibration ≠ test.** Every threshold/weight/hyperparameter is frozen before the test split is scored.

### 8.3 Metrics

**Primary:**

- Risk-coverage curve and AURC.
- Coverage at residual risk ≤ 1%, 2%, 5%.
- **Oracle decomposition** (caught / observable-but-missed / undetectable) — headline; report with the combined false-review rate of the union.

**Operational:**

- Escaped errors per 10k accepted; false reviews per 10k correct.
- Error capture at 5/10/20% review budget, at **output and document** levels (**incident-level optional** — needs root-cause grouping).
- Cost per 1k outputs (LLM calls, tokens) and latency.
- **Cost/risk/coverage Pareto frontier** — the home of H1(b).

**Reliability (not a novelty claim):**

- Observed residual risk + a **95% binomial upper bound**, computed at document level. *(Conformal risk control dropped — invalid under shift.)*

**GT quality:**

- Report every headline number twice: on all adjudicated errors, and on `gt_status = certain` + legible sources only. Report ambiguous/illegible separately. (Protects the frontier claim from GT noise.)

**Diagnostic:**

- Error-detection AUPRC; recall per failure family; unique capture + marginal utility per channel; rate of CONFLICTED and INSUFFICIENT states and the error rate within each. (Calibration/severity optional/secondary.)

**Uncertainty:**

- 95% CIs by **document-level bootstrap** (never field-level). **Count errors, not outputs; target ≥200 natural errors per testbed.**

**Validity (mandatory alongside headline numbers):**

- The placebo control (§9, E5b): headline gains are reported *with* the placebo result. A gain that survives placebo is a real result; one that collapses is a shortcut.

### 8.4 Baselines

**Equal cost (0 extra LLM) — must beat:** extractor log-prob/verbalised confidence; existing production rule (legacy ROI, Signal classifier, Table Trust ≥ 85); existing rules-based NTP.
**Higher cost (≥1 LLM/VLM) — show a better trade-off, cost on the plot:** self-consistency (k=3–5); same-model self-check; second-model agreement (dual-LLM); second parser agreement (MinerU vs GLM, tables); source-grounded VLM judge.

> **OPEN (Phase A):** confirm whether extractors expose token log-probs, and the budget for self-consistency / VLM-judge baselines (run on a subset if budget is tight).

---

## 9. Experiments

**Work needed** legend: **Re-score** = recombine/re-run the cheap channels on existing outputs (no re-extraction) · **Annotation** = human labelling · **New** = build something (e.g. mutation functions, dropout) · **Rerun** = run the verifier on a different data slice · **Witness run** = offline second-OCR · **Stats** = a calculation.


| ID         | Experiment (plain)                                                                                           | Tests                  | Work needed                                                       | Verdict                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------ | ---------------------- | ----------------------------------------------------------------- | ---------------------------------------- |
| **E0**     | Load all system outputs + baselines into one record format with continuous per-channel logs, on clean splits | foundation             | **Re-score** existing + run baselines                             | Keep (refined)                           |
| **E1**     | Main comparison: risk-coverage + cost vs baselines                                                           | H1                     | **Re-score** (uses E0)                                            | Keep — Fig 2                             |
| **E2**     | Channel / family ablations (each channel on/off)                                                             | H1, H2                 | **Re-score** (recombine logs + re-fit cheap fusion — *no re-run*) | Keep                                     |
| **E3a**    | Controlled corruption (mutate the *output*, then re-score)                                                   | H2, H5                 | **New** (mutation functions) + re-score                           | Optional gap-filler (rare families only) |
| **E3b**    | Natural-error atlas (adjudicated real errors, labelled by family)                                            | H2, H5                 | **Annotation** + re-score                                         | Keep (critical) — Fig 3                  |
| **E4**     | Complementarity: unique capture + marginal utility                                                           | H3                     | **Re-score**                                                      | Keep — Fig 4                             |
| **E4b**    | Shared-OCR overlap (lineage)                                                                                 | H3                     | **Re-score** (needs witness)                                      | Optional                                 |
| **E4c**    | Oracle ceiling + error decomposition (the frontier)                                                          | H5                     | **Re-score** (per-channel thresholds)                             | Keep — headline                          |
| **E5**     | Sufficiency estimator + evidence dropout                                                                     | H4                     | **New** (dropout) + re-score                                      | Optional (pilot-gated)                   |
| **E5b**    | Placebo controls (shuffled evidence must collapse the gain)                                                  | validity               | **Re-score** (permute logs — cheap)                               | Keep (mandatory)                         |
| **E6**     | Shift: new templates/vendors/time; extractor swap                                                            | H1, H6                 | **Re-score** on a different slice; extractor-swap = **new run**   | Keep (partly done)                       |
| **E6b**    | Risk certification (binomial bound)                                                                          | reliability            | **Stats** calc                                                    | Refine (binomial only)                   |
| **E-cost** | Free vs cheap-OCR vs LLM (catch vs cost)                                                                     | H1                     | **Witness run** (offline)                                         | Optional (pilot-gated)                   |
| **P1**     | (prep) Independent-witness channel for fields (docTR on crops, offline)                                      | feeds E2/E4/E4c/E-cost | **Witness run** (offline; needs images)                           | Optional. Tables: already in E0          |
| ~~E3c~~    | ~~Corruption specificity~~                                                                                   | —                      | —                                                                 | Removed                                  |
| ~~E7~~     | ~~Weak supervision~~                                                                                         | —                      | —                                                                 | Removed (out of scope)                   |


### 9.1 Failure families (grouped for statistical density; freeze after first ~100 natural errors)

**Fields (~7):**


| Family                                  | Includes                                                | Frontier candidate |
| --------------------------------------- | ------------------------------------------------------- | ------------------ |
| Misread                                 | one-char, one-digit                                     | ⭐                  |
| Wrong-but-plausible value               | wrong value present in source, wrong duplicate instance | ⭐                  |
| Wrong association                       | adjacent-field swap, cross-field copy                   | partly             |
| Type violation                          | e.g. date in currency field                             | no                 |
| Hallucination                           | value absent from source                                | no                 |
| Omission / false empty                  | populated → empty                                       | no                 |
| **Partial / truncated value** *(added)* | value cut off                                           | maybe              |


**Tables (~5):**


| Family                           | Includes                                            | Frontier candidate |
| -------------------------------- | --------------------------------------------------- | ------------------ |
| Cell content misread             | char/digit inside a cell                            | ⭐                  |
| Row / column omission            | dropped row/column                                  | no                 |
| Merge / split                    | rows/cells combined or split                        | no                 |
| Structural corruption *(merged)* | cell shift, span corruption, structural permutation | no                 |
| Crop truncation                  | missing edge evidence                               | no                 |


**Use of failure families:** they are the *rows of the detectability map* (H2), the definition of the *frontier* (H5), and the drivers of corruption (E3a). They organise the **miss side** (caught vs escaped / FN), not the false-alarm side.

### 9.2 Annotation (natural errors)

- Annotate `failure_family`, `severity`, `source_observability`, `gt_status`, and (optional) incident/root-cause. Which channels exposed each error is *computed*, not annotated.
- Adjudication is blind to verifier outputs; mandatory for every frontier-bucket error + a random 20% of the rest.
- Two annotators, Cohen's κ on 20% overlap, target κ ≥ 0.6; one-page labelling guide.

---

## 10. Ablations

Grouped under one Analysis section (as subsections/a table), not separate sections.

**Core (always feasible):**

- **A1 — Remove each evidence family (L0–L4).** *Conveys:* how much each *type* of clue contributes; justifies each family. Run as the family-level rollup of E2 (re-score on logs).
- **A2 — Support-only vs contradiction-only signals.** *Conveys:* whether the power comes from evidence that *confirms* vs *contradicts* the value; explains the mechanism. Cheap re-score.

**Conditional (only if the matching optional component is built):**

- **A3 — Independent vs same-engine OCR witness (tables only).** *Conveys:* that witness *independence* — not just a second text source — is what catches errors (a positive validation of the design). Needs both witnesses; feasible for tables, not fields.
- **A4 — Remove sufficiency gating.** *Conveys:* whether sufficiency actually helps decisions — this *is* the H4 pilot. Only if sufficiency is built.
- **A5 — Corruption-only vs natural-error calibration.** *Conveys:* whether tuning on synthetic errors transfers to real ones (the transfer gap is itself a finding). Only if E3a runs.

**Dropped (with reasons):**

- *Dependency/provenance ablation* — we already know channel provenance from the method; no experiment needed.
- *Native-vs-common-fusion* — proving a tuned system works with its own combiner is trivial (see §6.5).
- *Field-specific vs typed-generic as an experiment* — needs a full rewrite; not worth the effort.

**Kept as a one-line framing note (not an experiment):** categorise the existing field-specific patches into ~5 general types (cross-field-copy, source-absence, type-mismatch, label-value-mismatch, value-position). A labelling exercise that answers "is this just bespoke hacks?" without a rewrite.

---

## 11. Paper structure and figures

Standard NAACL long-paper skeleton (8 pages). **Abstract and Limitations are mandatory; Ethics is advisable** (both unnumbered, not counted in the page limit). Channels are introduced before the system (the system is defined as bundles of channels). Ablations, robustness, reliability, and validity are grouped under one Analysis section.

```
Abstract                                      (mandatory)

1  Introduction
     - the problem; "verification without a second model" framing
     - the 3 contributions; one dataset-anchored teaser number
2  Related Work
3  Approach
     3.1  Problem setup: zero-LLM constraint, decision = f(E,A), evidence states
     3.2  Evidence channels (L0–L4 taxonomy — the building blocks)
     3.3  System: router, three modes as channel bundles, fusion   [Fig 1]
4  Experimental Setup
     - testbeds/data; error definitions; splits (independent calib vs test);
       baselines; metrics
5  Results
     5.1  Main selective-prediction results + cost vs baselines     [Fig 2]
     5.2  The detectability frontier (oracle decomposition)         [Fig 6]  ← pillar
6  Analysis
     6.1  Detectability map (family × channel)                      [Fig 3]
     6.2  Complementarity (unique capture, marginal utility)        [Fig 4]
     6.3  Robustness under shift                                    [Fig 5]
     6.4  Reliability (risk bound) & Validity (placebo)             (merged)
     6.5  Ablations
7  Conclusion

Limitations        (mandatory, unnumbered, not in page count) — the frontier as a fundamental limit; checkboxes/signatures out of scope
Ethics Statement   (advisable, unnumbered, not in page count) — proprietary / privacy data
References          (not in page count)
```


| Figure | Content                                                                     |
| ------ | --------------------------------------------------------------------------- |
| Fig 1  | Unified system: router → modes → channels → fusion → evidence state         |
| Fig 2  | Risk-coverage curves (A/B/C panels) with baselines + cost — **headline**    |
| Fig 3  | Detectability heatmap (family × channel; corruption + natural side by side) |
| Fig 4  | Marginal utility vs standalone verifier accuracy                            |
| Fig 5  | Performance under shift                                                     |
| Fig 6  | Error decomposition: caught / observable-but-missed / undetectable          |


**Notes:** the held-out test set *is* the main results (§5.1) — there is no separate held-out section; shift (§6.3) is the deliberately-different distribution. **Must not read as** "§ROI, §Signal, §Table scorer" stapled together.

---

## 12. Novelty position

**Do not claim novelty for:** abstaining when uncertain; "using evidence"; support/refute/insufficient classification; comparing two models; diversity-beats-accuracy (H3 is a known principle). These guardrails prevent over-claiming.

**Defensible novelty:**

> A unified study of **document-native, zero-extra-LLM** verification across extraction granularities (fields and tables), with explicit evidence availability, measured verifier complementarity, failure-family detectability, and — the pillar — a **quantified detectability frontier** validated on both controlled and natural errors.

*(The related-work review and citations are compiled during paper writing, not here. Areas to position against, for reference only: reference-free QE, selective prediction / risk control, LLM uncertainty, fact verification, ensemble diversity, document-AI evaluation.)*

---

## 13. Scope

**In:** structured-field, unstructured/semi-structured-field, and table verification with zero extra LLM calls; **detection only**.

**Out (with reasons):**

- **GT-free / weak-supervision claims** — the systems are trained/tuned on ground truth (ROI blueprints from golden data; Signal classifiers on GT; thresholds on GT), so a GT-free claim would be *false* and easily disproven.
- **Routing / refinement / repair actions** — this paper evaluates *detection* ("is the output wrong?"), not *repair* ("how do we fix it?"), which is a separate research question with its own evaluation. Including it would balloon scope and dilute the story.
- **Relational / cross-field consistency (L4)** — checking that extracted values agree with each other (sums, date ordering, table totals) is *business-logic* checking, not extraction verification, and would need hundreds of domain-specific constraints. Out of scope; noted as future work.
- **Cross-document evidence; adaptive verifier-routing policies; RL / training the extractor against the verifier** — separate research directions, deferred.
- **Checkboxes, signatures, stamps** — not covered by the current systems; reported as a coverage gap.

---

## 14. Reproducibility

- **Private data and production code stay private** — there is no requirement to release them.
- **Public benchmarks now cover all three modes (not just tables)** — each a first-class, headline result, so the *core method is reproducible on public data for every mode*:
  - **Tables:** RD-TableBench (held-out); optionally a second public set (FinTabNet/PubTables-1M) or DocILE LIR.
  - **Structured fields (ROI):** **FATURA** (synthetic, 50 templates × 24 fields) + **FARA** (real US-gov forms).
  - **Unstructured fields (Signal):** **RealKIE** (finance, variable-layout); optionally **DocILE** (which doubles as a public tables leg via LIR).
  - Details, sizes and licensing are in the companion dataset-exploration doc.
- **Describe the method in full** (standard). Optionally release non-proprietary artifacts: the failure taxonomy, the corruption generator, the evaluation harness (no private data).

---

## 15. Risks (internal planning — not paper content)

| Risk | What it means | Why it's here | Mitigation |
|---|---|---|---|
| LLM baseline clearly wins on coverage | self-consistency / VLM judge may catch more errors than the zero-LLM method | real possibility — it's why H1(b) is a *trade-off* claim, not "match the LLM" | reframe on cost-per-coverage + the frontier |
| Too few natural errors for tight CIs | fewer than ~200 errors per testbed → wide, inconclusive error bars | statistical power comes from the error count, and data may be limited | count early; pool doc types; add public sets |
| "Three systems stapled together" | reviewers read it as three separate systems, not one | the #1 framing risk — the whole reframe exists to avoid it | one formulation, one output, one metric set; cross-mode figures |
| The "undetectable" bucket is GT noise | the frontier is attacked as "those aren't undetectable, your GT is just wrong" | it directly threatens the novelty pillar (H5) | blind adjudication; headline numbers on certain + legible GT only |
| Verifier learns shortcuts | gains come from field identity / doc-type / prevalence, not real evidence | a validity threat that would make the results meaningless | placebo controls (E5b) |
| Shared upstream OCR inflates complementarity | channels look complementary but secretly share the same OCR | it threatens the complementarity finding (H3) | witness independence; the tables-only same-OCR ablation (A3) |

---

## 16. Open questions for kickoff

1. Which extractors expose token log-probs? If none, which equal-cost confidence proxy?
2. Budget for self-consistency and VLM-judge baselines (full set vs subset)?
3. Do the field test sets have stored **page images** (needed for the optional P1 witness)?

---

## Bottom line

> Given a Document AI output, using no additional LLM calls: what observable evidence could reveal that it is wrong? Which failure mechanisms can each channel expose, how complementary are they, and how much automation is safe versus LLM-based verification — while being honest about the errors that no evidence can catch.

