# Evidence-Based Verification for Document AI
## Research Specification v2 (merged)

**Status:** Draft for kickoff · **Date:** 2026-09-23 · **Owners:** _TBD_
**Supersedes:** `research_brief_evidence_based_verification.md`, `evidence_based_document_ai_verification_research_spec_v1.md` and `evidence_verification_v2_recommended_additions.md` (merged in as v2.1)
**Source material (this folder):** `StructuredNTP/` (ROI-based NTP), `UnstructuredNTP/` (single-LLM signal NTP), `TableScorer/` (Table Trust Scoring)

---

## 0. TL;DR

- **What "NTP" means here.** At inference time we want to know whether an extraction can be trusted **without making any additional LLM call**. The extractor runs once. Verification uses only non-LLM evidence from the document: OCR, layout, structure, learned priors and lightweight classifiers.
- **We already have three zero-extra-LLM verifiers**, covering two output types:
  - **NER fields in template-based documents:** ROI-NTP.
  - **NER fields in unstructured documents:** Signal-NTP.
  - **Tables:** Table Trust.

  Each was built and evaluated on its own terms. No shared protocol, baselines or failure analysis exists yet.
- **Thesis.** Every output leaves traces in its source document. Different evidence channels expose different failure mechanisms. How much we can safely automate depends on which evidence is available, how complementary those channels are, and which failure types they can detect at all.
- **Headline claim to test.** With zero extra LLM calls, document evidence should:
  - beat equal-cost baselines, and
  - match or approach LLM-based verification (dual-LLM, self-consistency, VLM judge) at a fraction of the cost.

  Some errors are undetectable from any available evidence. The system should say so explicitly instead of calling those outputs "verified".
- **NTP is the application, not the contribution.** The contribution is the formulation, a common evaluation protocol, the map of which failure families each evidence channel can detect, and the complementarity analysis.
- **Start here.** Phase A (week 1) fixes the definitions and the record format. There is a go/no-go gate at week 5 (§13).

---

## 1. Framing

### 1.1 Claims we can and cannot make

| Claim | OK? |
|---|---|
| "Verification **without inference-time GT**" | ✅ Ground truth is used only offline: for ROI blueprints, classifier training and threshold tuning. |
| "**Zero additional LLM calls** at inference" | ✅ This is the defining constraint of the method class. |
| "GT-free verification" / "GT-free accuracy" | ❌ False today. ROI is built from golden data and the Signal-NTP classifiers are trained on GT. |
| "We determine whether the LLM is correct" | ❌ We measure the evidence for and against an output, which is not the same thing. |

### 1.2 Correctness ≠ verifiability

A verifier cannot answer "is this output correct?" It can answer "**what observable evidence supports or contradicts it?**" Every channel has blind spots:

- **ROI-NTP:** `JOHN SMYTH` extracted from exactly the right box passes the check.
- **Signal-NTP:** the value appears in the OCR text, next to the right label, with the right type, and still passes if the LLM and the OCR share the same misread.
- **Table Trust:** the image says `8,357`, while the parser, the docTR witness and a VLM all read `8,857`. With no arithmetic or repetition constraint, nothing observable can tell the difference.

### 1.3 Research question

> Given a Document AI output (a field or a table), and using **zero additional LLM calls**, what observable document evidence could reveal that the output is wrong? Which failure mechanisms can each evidence channel expose, and how complementary are the channels? How much automation is safe at a bounded residual error, compared with LLM-based verification, when only a subset of the evidence is available?

**Working title:** "Verifying Document AI Without a Second Model: Evidence-Based Checks for Field and Table Extraction"
**Alternative:** "Beyond Model Agreement: Evidence-Based Verification of Document AI Outputs Without Inference-Time Ground Truth"

---

## 2. Current state (from the docs in this folder)

### 2.1 ROI-NTP (template-based structured documents, NER fields)

- **How it works.**
  - A single LLM extracts the fields.
  - Each value is mapped to OCR bounding boxes and scored against a per-field ROI built from golden data (5–95 percentile union box, with IQR outlier filtering): `overlap_w·overlap + center_w·center + iou_w·IoU ≥ threshold`.
  - Weights and threshold are grid-searched per field, minimising false negatives first.
  - A document is NTP only if every field is NTP.
- **Scale:** 5 document types (1008, CD, URLA, LE, FHA) and 219 fields.
- **Bugbuster results:**

| Doc type | ROI | Dual-LLM |
|---|---|---|
| 1008 | 90.3% | 80.0% |
| CD | 85.0% | 72.5% |
| URLA | 74.1% | 75.6% |
| LE | 98.6% | 100% |
| FHA | 73.8% | 100% |

- **Known gaps:**
  - It depends on the template.
  - It cannot handle checkboxes, signatures or stamps.
  - Duplicate values: it takes the first match, which may be the wrong instance.
  - **It cannot detect a wrong value in the right location.**
- ⚠️ **Issues to resolve:**
  - The local and Bugbuster runs disagree. Locally, 1008 scores 94.5% and FHA 71.8%, against a rule-based baseline of 85.1%.
  - "NTP accuracy" is never defined.
  - The weights and threshold may have been tuned on the same golden data they're evaluated on.

### 2.2 Signal-NTP (unstructured documents, NER fields)

- **How it works.** Five signals feed per-document-type tree classifiers (RF, GBM, XGB, LGBM): `format_valid`, `keyword_context`, `source_context`, `value_in_text` and `label_value_distance`. There is an optional 3-tier pair router that sends outputs to NTP, LLM_REVIEW or HUMAN_REVIEW.
- **Results on a held-out random 20% split:**

| Doc type | NTP rate (coverage) | NTP accuracy (1 − residual risk) | Error catch |
|---|---|---|---|
| Appraisal | 74.9% | 98.2% | 76.0% |
| Credit Report | 63.5% | 97.4% | 82.4% |
| Compliance Agreement | 60.2% | 97.1% | 81.8% |

- **This is already a selective-prediction setup.** Residual risk is about 2–3%, and **17–24% of errors escape**. That is the baseline to improve.
- ⚠️ **Issues to resolve:**
  - The random split needs to be replaced with document-, vendor- or template-disjoint splits.
  - Case-specific hardening rules need to become typed mechanisms (§6.4).
  - **Corpus mismatch.** This PDF covers Appraisal, Credit Report and Compliance Agreement. Earlier notes mention CICF, Escrow, FPL and HOI with 7 signals and more than 10k evaluations. Pick the canonical corpus in week 1.

### 2.3 Table Trust (tables)

- **Inputs:** table HTML (from MinerU, GLM or Parse), an optional crop image, and an optional **independent** OCR witness (docTR or native OCR). The same engine's block text is explicitly excluded as a witness.
- **Core signals (weights):** crop/boundary (20, off by default), geometry/topology (25), structural plausibility (25) and content conservation (25).
- **Post-core checks:** concat-merge, missing-content, token layout and reading order.
- **Outputs:** `base_trust_score`, `reason_codes` and `failure_family_hint`. The accept rule is score ≥ 85.
- **Evaluation harness:** `evaluate_rdbench_trust.py` runs on **RD-TableBench, which is public**. This is the easiest testbed to reproduce and to scale.
- **Already aligned with this paper:**
  - The witness-independence rule, which is exactly the complementarity idea.
  - The failure-family hints, which are exactly the detectability idea.
- ⚠️ **Issues to resolve:**
  - Weights, threshold and post-core rules were hand-iterated on the same benchmark they're evaluated on, so we need a frozen held-out split.
  - The current evaluation is small (a few dozen reviewed tables).
  - There is no table-level definition of an error yet (§8.1).
  - The code lives at `scripts/extract/table_extraction/`, outside this folder.

### 2.4 Where the current evidence sits in the taxonomy

| System | Output-internal | Source-grounding | Independent witness | Prior | Relational |
|---|---|---|---|---|---|
| ROI-NTP | — | weak (OCR box match) | — | ✓ ROI | — |
| Signal-NTP | ✓ format | ✓ value/label/context | — | (learned by the classifier) | — |
| Table Trust | ✓ topology, structure | ✓ crop bands/valleys | ✓ docTR conservation | — | — |

**Two gaps follow from this table:**
- **The field testbeds have no independent witness channel.** `value_in_text` likely uses the same OCR the LLM saw.
- **No system has a relational channel.** Both are fixed in §6.4.

---

## 3. Research object

For each prediction unit:

| Symbol | Meaning |
|---|---|
| `x` | source document or region |
| `y` | primary Document AI output |
| `c` | latent correctness of `y` (known only in offline evaluation) |
| `E = {e₁…e_k}` | evidence observations, one per channel |
| `A = {a₁…a_k}` | channel availability (did the channel run and apply?) |
| `D` | dependency or provenance tag per channel (a label only; real dependency is *measured* in §5.3) |
| `F` | failure family (annotated on errors) |
| `R` | estimated residual error risk |
| `S` | evidence sufficiency (§5.2) |
| `decision` | accept / recheck / human review |

### 3.1 Per-channel evidence record

```json
{
  "channel": "independent_ocr",
  "family": "independent_witness",
  "available": true,
  "applicable": true,
  "polarity": "support | contradict | neutral",
  "strength": 0.81,
  "dependency_group": "ocr_engine_b",
  "source_artifact": "page_image",
  "upstream_engine": "doctr",
  "preprocessing_lineage": ["render_300dpi", "deskew_v2"],
  "shared_ancestor_with_primary": false,
  "cost_ms": 37,
  "llm_calls": 0,
  "reason_codes": ["VALUE_MATCH_NORMALIZED"]
}
```

`available` means the channel ran. `applicable` means it can say something about this particular output. For example, ROI isn't applicable when the value occurs in several places, and the arithmetic check isn't applicable when a table has no totals row.

**Evidence lineage.** `dependency_group` is only a label we assign by hand. What really matters is whether two channels share upstream information: the same OCR, the same render or crop, the same layout model. In the example below, `value_in_text` is *not* independent of the extractor, even though it lives in a separate module:

```text
PDF image ─┬─> OCR-A ─> primary extractor
           ├─> OCR-A ─> value_in_text verifier       (shared ancestor)
           └─> OCR-B ─> independent witness          (independent)
```

Lineage fields are **mandatory** from Phase A onward. Auditing them is how we answer open question §16.3.

### 3.2 Per-output record (the unit of every analysis)

```json
{
  "output_id": "…", "testbed": "A|B|C",
  "doc_id": "…", "doc_type": "…", "template_id": "…", "vendor": "…", "timestamp": "…",
  "extractor": "…", "field_or_table": "…",
  "prediction": "…", "gt": "…", "is_error": true,
  "gt_status": "certain|disputed|source_ambiguous|corrected_gt",
  "error_family": "…", "error_severity": "minor|major|critical", "source_observability": "legible|ambiguous|illegible",
  "incident_id": "…", "root_cause_family": "…",
  "channels": [ { "...per-channel record..." } ],
  "verifier": {
    "estimated_error_risk": 0.004,
    "evidence_state": "CORROBORATED|CONTRADICTED|CONFLICTED|INSUFFICIENT",
    "evidence_sufficiency": 0.84,
    "possible_blind_spots": ["character_substitution"],
    "reason_codes": []
  },
  "legacy_scores": {"roi": null, "signal_clf": null, "table_trust": null},
  "baseline_scores": {"logprob": null, "self_consistency": null, "self_check": null, "dual_llm_agree": null, "vlm_judge": null},
  "cost": {"llm_calls": 1, "tokens": 0, "latency_ms": 0}
}
```

The JSON itself is not a contribution. Its job is to force every experiment to separate evidence type, availability, dependency and cost.

---

## 4. Evidence states and taxonomy

### 4.1 Four evidence states

| State | Meaning | Default policy |
|---|---|---|
| `CORROBORATED` | At least one material channel supports the output, and no material contradiction exists. | Auto-accept (NTP) |
| `CONTRADICTED` | Material contradiction, and no material support. | Review / re-extract |
| `CONFLICTED` | Material support and material contradiction both present. | Review (log for analysis) |
| `INSUFFICIENT` | No applicable channel gives a material signal either way. | Policy decision: review, cheap recheck, or accept against a risk budget |

- **These are evidence states, not correctness labels.** Material thresholds θ_support and θ_contradict are fit on the calibration split only.
- **Report two variants of CORROBORATED:** support from at least one channel (k=1), and support from at least two *different dependency groups* (k=2).

### 4.2 Evidence taxonomy

| Level | Family | Tests | V1 channels |
|---|---|---|---|
| L0 | Output-internal | Is the output legal and plausible on its own? | `format_valid`, HTML geometry/topology, structural plausibility |
| L1 | Source grounding | Does the source contain or support it? | `value_in_text`, `keyword_context`, `source_context`, `label_value_distance`, crop bands/valleys |
| L2 | Independent witness | Does a separately produced observation agree? | docTR or native-OCR conservation (tables); **new:** independent OCR on the field region (§6.4) |
| L3 | Historical prior | Is it consistent with learned structure? | ROI blueprint, empty-field prior |
| L4 | Relational | Is it consistent with other facts in the same document? | **new, at least one:** cross-field constraints and table totals (§6.4) |
| — | Cross-document | Corroborated by other documents? | **Out of scope for V1** |

---

## 5. Core constructs

### 5.1 Detectability

A wrong prediction falls into one of three kinds:
- **Directly detectable** with the current evidence.
- **Partially detectable.**
- **Indistinguishable from a correct prediction** with the current evidence.

For each failure family *f* and channel *k*, at a fixed false-review rate (proposal: 5% of correct outputs flagged):

```text
Detection(f, k) = P(channel k gives material contradiction | output wrong, family f)
```

We estimate this twice: once on **controlled corruptions** (E3a) and once on **natural errors** (E3b). **Whether the corruption estimates transfer to natural errors is itself a result**, whichever way it comes out.

Target result shape: *"Row omission is highly observable through topology plus OCR conservation. Single-character substitution is barely observable when the extractor and the OCR share the same visual ambiguity."*

### 5.2 Evidence sufficiency (secondary construct)

This is the fraction of plausible failure space that the available **and applicable** evidence can inspect:

```text
S(o) = Σ_f w(t,f) · Detectable(f, A_applicable(o))
```

- `w(t,f)` is the prevalence of failure family *f* among natural errors for output type *t*.
- `Detectable(f, ·)` is estimated from E3, preferring natural-error estimates. For channel sets, the value is measured jointly, never multiplied as if channels were independent.
- **Pitfall:** if S depends only on output type and availability, it collapses into a small lookup table. Per-instance **applicability** is what makes it vary between outputs, for example duplicate values present or absent, a totals row present or absent, or OCR tokens available or not.
- **Why it matters:** low risk with high S ("we checked and saw no problem") is a different situation from low risk with low S ("we saw no problem, but couldn't check the likely failure modes").
- **Scope:** this is tested mainly under evidence dropout and distribution shift (H4). **The paper does not depend on it.**

### 5.3 Conditional complementarity (replaces "independence")

On the primary extractor's errors, let z_k = 1 if verifier *k* exposes the error. We measure:

- pairwise detection overlap and correlation of z_i and z_j;
- **unique capture**: errors that only verifier *k* exposes;
- `MarginalUtility(j | S) = ErrorCapture(S ∪ {j}) − ErrorCapture(S)`;
- `CostAdjustedUtility(j | S) = MarginalUtility(j | S) / Cost(j)`.

This tests the claim that a weaker verifier that fails *differently* can be worth more than a strong verifier that repeats the primary model's mistakes.

**Link to lineage.** Report unique capture broken down by `shared_ancestor_with_primary` (true or false). With only 2–3 OCR engines, this analysis is **descriptive**; we don't have enough data points to fit a trend. The causal test is Ablation 3 (swap in the parser's own OCR).

### 5.4 Oracle observability ceiling and the error decomposition

This separates **"the evidence couldn't see it"** from **"the fusion model didn't use it"**.

**Definition.** Each channel *k* is set to its own threshold at a fixed false-review rate (5% of correct outputs flagged). A natural error counts as *observable* if at least one available channel gives a contradiction at that threshold:

```text
OracleCapture = |errors with ≥1 channel contradicting at its 5%-FRR threshold| / |all primary errors|
```

> ⚠️ **The threshold is mandatory.** Without a fixed false-review rate per channel, a loose enough channel flags everything and the oracle is trivially 100%. Always report the **combined false-review rate** of the union alongside OracleCapture.

**Headline decomposition** (this makes the detectability frontier concrete):

```text
100% primary errors  (excluding gt_status ∈ {disputed, source_ambiguous}; reported separately)
 ├── X% observable by ≥1 available channel
 │     ├── Y% captured by the fused verifier
 │     └── (X−Y)% fusion failures         → modelling problem
 └── (100−X)% observable by no channel     → detectability frontier (evidence problem)
```

---

## 6. Testbeds

### 6.1 Testbed A: template-based structured fields

The mortgage documents from §2.1. ROI becomes **one channel** (L3), not a standalone algorithm.

### 6.2 Testbed B: layout-variable fields

The Signal-NTP corpus from §2.2. Which corpus is canonical is decided in week 1.

### 6.3 Testbed C: tables

We evaluate whole-table reliability plus the diagnostic failure families. The data is RD-TableBench (a held-out split) plus internal tables. We need **hundreds of labelled tables**, with at least 200 errors.

### 6.4 Changes the existing systems need before they can be experiment arms

1. **All three systems:** emit the §3.1 and §3.2 records, with continuous scores and per-channel polarity and strength. A binary NTP label alone is not enough.
2. **ROI-NTP:**
   - Expose the raw overlap, center and IoU components.
   - Score every occurrence of a duplicate value and take the best match, instead of the first.
   - Set `applicable=false` when the value occurs more than once.
3. **Signal-NTP:**
   - Replace random splits with disjoint splits.
   - Rewrite field-specific patches as typed mechanisms: `type_incompatibility`, `source_absence`, `label_value_mismatch`, `cross_field_copy` and `value_position_inconsistency`. Patches that can't be generalised get dropped and reported in an ablation.
4. **Table Trust:**
   - Freeze a version and its threshold.
   - Expose each core signal separately.
   - Label table errors using the §8.1 definition.
5. **New L2 channel for fields (no LLM):** run a second OCR engine (docTR) on the field's ROI or source region and compare the normalised text with the prediction. Without this, the field testbeds have no independent witness and H1 is untestable there.
6. **New L4 channel (no LLM), at least one per granularity:**
   - **Fields:** cross-field constraints, such as date ordering, sums (loan amount against its components) and the same entity repeated across fields.
   - **Tables:** row and column totals and repeated values, where they exist.
   - If we can't build these by week 4, drop relational evidence from the V1 claims.
7. **Cost logging** in every arm, including `llm_calls`.

**Fusion:** logistic regression or a shallow tree is the **primary** fused verifier, because it shows what the evidence itself is worth. XGB/LGBM (the current Signal-NTP models) are reported for comparison.

---

## 7. Hypotheses

| ID | Hypothesis | Role |
|---|---|---|
| **H1: Zero-LLM verification** | With zero extra LLM calls, evidence fusion (a) beats **equal-cost** baselines on coverage at a fixed residual risk, and (b) **matches or approaches** LLM-based verification (dual-LLM, self-consistency, VLM judge) at ≤ 0.5× the cost. The same holds for scalar fields and for tables. | **Headline** |
| **H2: Complementarity** | Different evidence families expose statistically different failure families (E3 heatmap). | **Main** |
| **H3: Conditional utility** | A verifier's unique capture of the primary model's errors predicts its value in the stack better than its standalone accuracy does. | **Main** |
| **H4: Sufficiency-aware selection** | Conditioning acceptance on both risk and evidence sufficiency improves the risk-coverage trade-off **under evidence dropout and shift**. | Secondary |
| **H5: Detectability frontier** | A non-trivial share of real errors can't be distinguished under the available evidence, and flagging those blind spots explicitly reduces false claims of verification. | **Main** (most distinctive) |
| H6: Shift robustness | Source-grounded and witness channels (L0–L2) degrade less than priors (L3) under template or extractor shift. | Analysis |

"Model confidence is imperfect" is deliberately left out as a hypothesis: it's already well established. It is included as a baseline instead.

---

## 8. Evaluation protocol (identical across testbeds)

### 8.1 Error definitions (frozen in Phase A)

| Testbed | Unit | Error = |
|---|---|---|
| A, B | field | Normalised prediction ≠ normalised GT, using the existing per-type normalisers. Empty versus empty counts as correct. |
| C | table | **Primary:** TEDS(pred, GT) < τ, with τ fixed before any verifier is scored (proposal: 0.9). **Secondary:** any cell content mismatch. |

Also report **document-level** results for A and B (a document is accepted only if all its fields are), because production routes whole documents.

### 8.2 Splits

- **Main:** document-disjoint, and template- or vendor-disjoint where IDs exist. No random field-level splits.
- **Calibration and test are separate.** Every threshold, weight and hyperparameter (ROI grid, Table Trust weights and the 85 threshold, θ_support and θ_contradict) is frozen before the test split is scored.

### 8.3 Metrics

**Primary:**
- Risk-coverage curve and AURC.
- **Coverage at residual risk ≤ 1%, 2% and 5%.** We don't promise 0.1%: at the current residual risk of about 2–3% it's unreachable, and it would need about 3,000 accepted outputs with zero errors per slice.

**Operational:**
- Escaped errors per 10k accepted outputs.
- False reviews per 10k correct outputs.
- Error capture at a 5%, 10% or 20% review budget, at three levels: **output, document and failure incident**. One OCR or rendering failure can corrupt ten fields, and counting it ten times inflates capture.
- Cost per 1k outputs (LLM calls, tokens) and latency per output.
- **The cost–risk–coverage Pareto frontier**: the non-dominated methods in (cost, residual risk, coverage) space. This is easier to compare than cost labels on a curve.

**Certified risk (reliability layer, not a novelty claim):**
- Report the **observed** residual risk and a **95% upper bound** separately. For example: "target 2%, observed 1.4%, upper bound 1.9%, at 63% coverage."
- **Method:** thresholds are chosen on the calibration split. The upper bound uses an exact binomial bound computed at **document level**, because field-level bounds assume independence that doesn't hold.
- Conformal risk control is an optional extension. It assumes exchangeability, so it is **not valid under shift** (E6); say so wherever it's reported.

**GT quality:**
- Report every headline number twice: on all adjudicated errors, and on `gt_status = certain` with legible sources only.
- Report ambiguous and illegible-source errors separately.

**Severity (secondary):**
- Unweighted error stays primary.
- Severity-weighted residual risk is reported as a secondary number. The levels:
  - **minor:** formatting only.
  - **major:** wrong fact.
  - **critical:** affects a downstream monetary, identity, eligibility or compliance decision.

**Diagnostic:**
- Error-detection AUPRC.
- Calibration (Brier score, ECE).
- Recall per failure family.
- Unique capture per channel and marginal utility.
- Rate of CONFLICTED and INSUFFICIENT states, and the error rate within each state.

**Uncertainty:**
- 95% confidence intervals by **document-level (or package-level) bootstrap**, never field-level, because fields in the same document are correlated.
- **Sample size:** count errors, not outputs. Aim for at least 200 natural errors per testbed.

### 8.4 Baselines

**Equal cost (0 extra LLM calls). Must beat.**

| Baseline | A | B | C |
|---|---|---|---|
| Extractor token log-prob / verbalised confidence | ✓ | ✓ | ✓ if available |
| Existing production rule (legacy ROI-NTP, Signal-NTP classifier, Table Trust ≥ 85) | ✓ | ✓ | ✓ |
| Existing rules-based NTP | ✓ | ✓ | — |

**Higher cost (≥ 1 extra LLM or VLM call). Match or approach at lower cost; cost is shown on the plot.**

| Baseline | A | B | C | Notes |
|---|---|---|---|---|
| Self-consistency / semantic uncertainty (k = 3–5) | ✓ | ✓ | ✓ (pairwise TEDS) | Most likely to hurt us |
| Same-model self-check | ✓ | ✓ | ✓ | |
| Second-model agreement (current dual-LLM) | ✓ | ✓ | — | Current production reference |
| Second parser agreement (MinerU vs GLM) | — | — | ✓ | Table analogue of dual-LLM |
| Source-grounded VLM judge (page or crop image) | ✓ | ✓ | ✓ | Expensive upper bound |

---

## 9. Experiments

| ID | Experiment | Tests | Output |
|---|---|---|---|
| **E0** | Replay the three existing systems and all baselines into §3.2 records, **without optimising them** | — | JSONL per testbed; `evaluate.py` |
| **E1** | Main selective-prediction comparison | H1 | **Fig 2** |
| **E2** | Channel and family ablations (§10) | H1, H2 | Ablation table |
| **E3a** | Controlled-corruption benchmark: hold the source fixed, mutate the output | H2, H5 | Detection(f, k) from corruption |
| **E3b** | Natural-error atlas: frozen extractors, adjudicated errors, annotated family, severity and observability | H2, H5 | Detection(f, k) from natural errors; **Fig 3**; test of whether corruption results transfer |
| **E3c** | **Corruption specificity.** For each (failure family, channel) pair, the **expected response is written down before the run** (e.g. one-digit change at the same location → ROI: no change; source text: contradict; type check: usually no change). Measure the intended response and the off-target alarm rate. | H2 | Two matrices: sensitivity and off-target activation |
| **E4** | Complementarity: unique capture and marginal utility for every channel and channel pair | H3 | **Fig 4** |
| **E4b** | Lineage analysis: unique capture broken down by shared-ancestor status (descriptive) | H3 | Table |
| **E4c** | **Oracle observability ceiling** and error decomposition (§5.4). **Mandatory.** | H5 | Decomposition figure (Fig 3 inset or a separate figure) |
| **E5** | Sufficiency estimator plus **evidence dropout** (remove OCR, geometry or priors) | H4 | **Fig 5a** |
| **E5b** | **Placebo evidence controls. Mandatory, and must run before Gate 1.** Replace each field's ROI with another field's ROI from the same template; take the OCR witness from another region or document; permute template IDs; pair relational checks with unrelated fields. **The verifier's advantage must collapse.** If it doesn't, it is exploiting shortcuts (field identity, document type, error prevalence) rather than the evidence. | Validity | Placebo table |
| **E6** | Shift: template or vendor held out; extractor or prompt swapped; temporal | H4, H6 | **Fig 5b** |
| **E6b** | Risk certification (§8.3) | — | Observed risk against the certified upper bound |
| E7 | Weak supervision (signals used as labelling functions) | — | **Stretch only**; no GT-free claim in V1 |

### 9.1 Failure families (starting taxonomy; refine on the first 100 natural errors)

| Family | Fields | Tables | Corruption example |
|---|---|---|---|
| Adjacent-field swap / wrong field association | ✓ | | borrower ← co-borrower name |
| One-character misread | ✓ | ✓ | SMITH → SMYTH |
| One-digit error | ✓ | ✓ | 8357 → 8857 |
| Wrong value that is present in the source | ✓ | | copy another number from the page |
| Wrong instance of a duplicated value | ✓ | | pick the second occurrence |
| Type violation | ✓ | | date in a currency field |
| Cross-field copy | ✓ | | ZIP copied into an ID field |
| Hallucinated value (absent from the source) | ✓ | ✓ | insert an unseen string |
| Omission / false empty | ✓ | ✓ | populated field → empty |
| Row or column omission | | ✓ | remove a row or column |
| Merge / split | | ✓ | combine or split source rows |
| Cell shift | | ✓ | move cells one column |
| Crop truncation | | ✓ | remove the final row or column evidence |
| Span corruption | | ✓ | wrong rowspan or colspan |
| Structural permutation | | ✓ | keep the words, alter the grid |

### 9.2 Annotation (natural errors)

- **Annotate:**
  - `failure_family`, `severity`, and `source_observability` (legible, ambiguous or illegible to a human);
  - `gt_status` (certain, disputed, source_ambiguous or corrected_gt);
  - `incident_id` and `root_cause_family`.

  Which channels exposed or wrongly corroborated each error is *computed* from verifier outputs, not annotated.
- **Adjudication:** blind to verifier outputs. It is **mandatory for every error that falls in the detectability-frontier bucket**, plus a random 20% of all other errors. Otherwise reviewers can argue that the "undetectable" bucket is partly annotation noise.
- **Incident proxy:** where root-cause labelling is too expensive, group the errors on a page that share a single OCR or rendering failure. Document-level grouping is the fallback.
- **Process:** two annotators, with Cohen's κ on a 20% overlap sample; target κ ≥ 0.6. We need a one-page labelling guide.

---

## 10. Ablations

1. Remove each evidence family (L0–L4).
2. Remove dependency and provenance information.
3. **Replace the independent OCR with the parser's own OCR.** This directly tests the witness-independence rule.
4. Support-only versus contradiction-only signals.
5. Remove sufficiency gating.
6. Calibrate on corruption only versus on natural errors.
7. Supervised fusion versus hand-weighted combination (for example, the legacy Table Trust weights).
8. Field-specific rules versus typed generic mechanisms.
9. CORROBORATED with k=1 versus k=2 dependency groups.

---

## 11. Paper structure and figures

```text
1 Introduction
2 Verification without inference-time ground truth (and without a second model)
3 Evidence taxonomy and formalization
4 Detectability, sufficiency and complementarity
5 Testbeds
6 Main selective-prediction results
7 Failure-family analysis
8 Evidence dropout and distribution shift
9 Cost / latency
10 Limitations and unobservable errors
11 Conclusion
```

| Figure | Content |
|---|---|
| **Fig 1** | Unified evidence architecture |
| **Fig 2** | Risk-coverage curves in 3 panels (A, B, C), with every baseline and cost annotated. **Headline figure.** |
| **Fig 3** | Heatmap of detectability by failure family and evidence channel (corruption and natural, side by side) |
| **Fig 4** | Marginal utility against standalone verifier accuracy |
| **Fig 5** | Performance under evidence dropout and shift |
| **Fig 6 / inset** | Error decomposition: observable and caught, observable but missed (fusion failure), not observable (detectability frontier) |

**Must not be:** "§3 ROI, §4 XGBoost NTP, §5 table scorer." That reads as three internal systems stapled together.

---

## 12. Novelty position and related work

**Neighbouring work (review in week 1):**
- **Reference-free quality estimation:** MT Quality Estimation (COMET-QE, the WMT QE tasks). This is the closest analogue.
- **Selective prediction and risk control:** Geifman & El-Yaniv, conformal risk control.
- **LLM uncertainty:** semantic entropy, SelfCheckGPT, verbalised confidence, P(True).
- **Verification with support/refute/insufficient labels:** fact verification (FEVER-style), attribution work (AIS, RARR), RAG verifiers.
- **Evidence-seeking and abstention in VLMs; source-grounded LLM judges.**
- **Weak supervision:** Snorkel, label models with correlated labelling functions.
- **Ensemble diversity and correlated errors:** Kuncheva.
- **Document AI evaluation:** TEDS and GriTS; VRDU; DocVQA calibration.

**Don't claim novelty for:** abstaining when uncertain; "using evidence"; support/refute/insufficient classification; comparing two models.

**The defensible novelty target:**

> A unified study of **document-native, zero-extra-LLM** verification evidence across extraction granularities (fields and tables), with explicit evidence availability, measured verifier complementarity, failure-family detectability, and selective acceptance under bounded residual risk.

The **detectability frontier** is the most distinctive contribution, provided it's backed by both the corruption results and the natural-error results.

---

## 13. Plan, gates and fallbacks

| Phase | Weeks | Work | Exit criterion |
|---|---|---|---|
| **A: Freeze the interface** | 1 | Prediction units, error definitions, §3 schema **including lineage, gt_status and incident fields**, failure taxonomy v0, dependency groups; resolve the §16 open questions; related-work table; **write down the expected responses for E3c** | Signed-off spec |
| **B: Replay** | 2–3 | Export ROI-NTP, Signal-NTP and Table Trust into §3.2 records unchanged; document-disjoint splits; count errors per testbed | ≥ 200 errors per testbed, or a plan to reach it |
| **C: Harness plus new channels** | 2–4 | `evaluate.py` (risk-coverage, bootstrap CIs, family recall); build the L2 field-OCR channel and one L4 channel | Metrics reproduce legacy numbers on legacy splits |
| **D: Baselines, E1/E2 and placebo** | 3–5 | Equal-cost and LLM-based baselines; simple fusion; **E5b placebo controls** | **Gate 1** |
| **E: Complementarity and detectability** | 6–8 | E3a/b/c annotation, corruption and specificity; E4/E4b; **E4c oracle ceiling** | Fig 3 and Fig 4; decomposition; κ ≥ 0.6 |
| **F: Sufficiency** | 8–9 | E5 sufficiency estimator plus dropout | Fig 5a |
| **G: Stress test** | 9–10 | E6 shift; E6b certification | Fig 5b |
| **Write** | 11–12 | Draft; replicate Fig 2 on at least one public set | Internal review |

**Gate 1 (end of week 5), go/no-go.** Go if, in **at least 2 of 3 testbeds**, the zero-extra-LLM evidence verifier:
- clearly beats the equal-cost baselines on coverage at 2% risk (bootstrap CIs don't overlap), **and**
- comes within about 5 points of coverage of the best LLM-based baseline, or beats it, **and**
- **passes the placebo controls (E5b)**: under placebo evidence, its advantage over the equal-cost baselines collapses. A gain that survives placebo is a shortcut, not a result.

**Fallbacks:**
- **Fields fail Gate 1 but tables pass:** publish **Table Trust standalone** (silent table-failure detection from independent evidence). This is the most reproducible piece, because RD-TableBench is public.
- **Tables can't get enough labelled errors:** publish a **field-only** study (A + B) with detectability and shift analysis.
- **Both fail:** write an internal technical report and reframe around the detectability and INSUFFICIENT analysis.

**Minimum viable paper:**
- 2 field domains plus 1 table domain.
- At least 2 extractor configurations (needed for extractor shift).
- At least 4 genuinely different evidence families.
- At least 5 failure families.
- At least 200 natural errors per testbed.
- The corruption benchmark.
- The equal-cost and LLM-based baselines.
- Risk-coverage and cost results.
- One real shift experiment.

---

## 14. Risks

| Risk | Mitigation |
|---|---|
| Self-consistency or the VLM judge clearly wins | Report it. Reframe around cost per unit of coverage, and around the detectability and INSUFFICIENT analysis. |
| Too few natural errors for tight confidence intervals | Count in Phase B; pool document types; add public sets. |
| Leakage from golden-data tuning | Freeze everything before test scoring; disjoint splits. |
| "Three systems stapled together" | One formulation, one schema, one metric set, and cross-testbed figures only. |
| Sufficiency is near-constant or circular | Use per-instance applicability; prefer natural-error estimates; keep it secondary (H4). |
| Corruption doesn't match natural errors | Report the transfer gap as a finding; base the main claims on natural errors. |
| The "undetectable" bucket is really GT noise | `gt_status` adjudication, blind to the verifier (§9.2); headline numbers reported on certain, legible cases. |
| The verifier learns shortcuts (field identity, document type, prevalence) | Placebo controls (E5b) are required before Gate 1. |
| Shared upstream OCR makes channels look complementary when they aren't | Lineage fields (§3.1), E4b, and Ablation 3. |
| Scope creep from all the added analyses | Only E4c and E5b are mandatory among the additions. E3c, E4b and E6b can be cut if the schedule slips. |
| Table Trust heuristics overfit to RD-TableBench | Held-out split plus a second public set (FinTabNet or PubTables-1M). |
| Proprietary data limits release | Release the evaluation code, taxonomy, corruption generator and public-set results. |

**Public data options:**
- **Structured fields:** VRDU (which has template-disjoint splits) and FUNSD.
- **Variable-layout fields:** CORD, SROIE and Kleister.
- **Tables:** RD-TableBench, FinTabNet and PubTables-1M.

---

## 15. Out of scope for Paper 1

- Cross-document (Relate) evidence as a main contribution.
- Adaptive "which verifier should run next" policies.
- RL, or training extraction against the verifier.
- Fully GT-free or weak-supervision claims (E7 is exploratory only).
- Routing, refinement and fallback actions: we evaluate detection, not repair.
- Checkboxes, signatures and stamps: reported as a coverage gap.
- Production workflow details that don't answer a research question.

---

## 16. Open questions for kickoff (resolve in Phase A)

1. **Which Signal-NTP corpus is canonical:** Appraisal/Credit/Compliance, or CICF/Escrow/FPL/HOI? Can we use both?
2. What does "NTP accuracy" measure in the ROI reports, and why do the local and Bugbuster runs disagree (especially FHA)?
3. Does `value_in_text` use the same OCR the extractor consumed? This decides whether the new L2 field channel is needed.
4. Are token log-probs available from the current extractors? If not, which equal-cost confidence proxy do we use?
5. What is the budget for the self-consistency and VLM-judge baselines over the full test sets?
6. Which cross-field and table-total constraints exist in the current document types, for the L4 channel?
7. Owners: who takes the harness, Testbed A, Testbed B, Testbed C and annotation?
8. What is the target venue and deadline? Back-plan §13 from it.

---

## Bottom line

> **Given a Document AI output, and using no additional LLM calls: what observable evidence could reveal that it is wrong? Which failure mechanisms can each evidence channel expose? How complementary are the channels? And how much automation is safe, compared with LLM-based verification, when only a subset of the evidence is available?**

The question is narrow enough to execute, broad enough to generalise beyond mortgage documents, and concrete enough to be proven wrong by experiment.
