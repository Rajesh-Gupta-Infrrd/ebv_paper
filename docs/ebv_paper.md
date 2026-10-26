# The Detectability Frontier of Document Extraction Errors: Verification Across Fields and Tables Without Extra Language- or Vision-Model Calls

*Living paper draft — ACL-family (ARR), long paper, double-blind. This file holds the best finalized version of each section. Version history per section lives in `ebv_<section>_versioning.md`.*

**Section status:** Related Work ✅ (draft v1) · Introduction ⏳ · Problem/Formulation ⏳ · Method/System ✅ (draft v1) · Experimental Setup ⏳ · Results ⏳ (pending experiments) · Analysis ⏳ (pending) · Limitations ⏳ · Ethics ⏳ · Abstract ⏳

> **Citation note:** author names/years below are drawn from our full-text reads and reviewer passes; a few keys are unverified (flagged in the versioning file). Verify all before submission.

---

## Related Work

**Confidence estimation and selective acceptance for document extraction.**  
A growing line of work attaches a confidence or trust signal to document key-information-extraction (KIE) outputs and uses it to decide which fields can be auto-accepted versus routed to a human reviewer. Early document-IE confidence engines such as HYCEDIS (Nguyen et al., 2021) fuse heterogeneous intermediate signals—OCR, box localization, and key–value recognition—through a conformal predictor, but are tied to a specific extraction stack. More recent work targets LLM/VLM extractors: ExtractConf (Kumar, 2026) shows that document- and OCR-grounded signals outperform raw token log-probabilities and fuses them with a gradient-boosted model; ConfBench (Roy et al., 2026) benchmarks the calibration of VLM confidence for document KIE under controlled degradations and reports an error-capture-at-review-budget metric; and Valid Per-Field Selective Risk Control (Gurram, 2026) adds distribution-free guarantees to the per-field accept/review decision. The closest system to ours on the fields side, Perception–Layout–Validation (Jin et al., 2026), decomposes confidence into interpretable perception, layout, and validation channels and gates straight-through processing with conformal risk control. However, these approaches share three limitations: they operate on fields only; they spend at least one additional LLM or VLM call at decision time (ExtractConf's two LLM passes; Perception–Layout–Validation's two-VLM comparison); and none quantifies which errors are undetectable from the available evidence.  

**Verification for tables, and across granularities.**  
Table extraction has a largely separate verification literature. Uncertainty-aware table extraction (Ajayi et al., 2025) and uncertainty quantification for table-structure recognition (Ajayi et al., 2024) flag unreliable cells, but do so by **aggregating the pipeline's own structure and OCR confidence scores** rather than verifying content fidelity against an independent reading of the page; QUEST (Thomas et al., 2025) instead trains a dedicated model to predict an extracted table's quality without ground truth at inference; and the recent DEC framework (Xiao et al., 2026) detects and repairs table-parse errors with an agentic vision-model controller.  Only RaV-IDP (Jha, 2026) spans multiple granularities—text, tables, and images—with a single label-free "reconstruction-as-validation" signal, with a vision-language-model fallback. However, these methods detect by reusing the pipeline's own confidence, by training a dedicated scorer, or by invoking a vision model, and none characterizes which table errors are fundamentally undetectable.

**Selective prediction and the detectability of errors.**
Deciding when to accept a prediction versus abstain is the classical problem of selective prediction (Chow, 1970; El-Yaniv and Wiener, 2010), extended to deep networks by Geifman and El-Yaniv (2017, 2019). A selective predictor's performance is standardly summarized by the risk–coverage curve and its area (AURC), and distribution-free guarantees on the accepted set are given by conformal risk control (Angelopoulos and Bates, 2023; Angelopoulos et al., 2024). In general classification settings, Rabanser and Papernot (2025) decompose the gap between a selective classifier and a perfect-ordering oracle into additive terms, including an irreducible Bayes-noise floor—the errors that no scoring rule can separate from correct predictions. Separately, Pandey et al. (2026) measure, for open-domain LLM question answering, that confident errors can be surface-indistinguishable from correct ones and are recoverable only by costly multi-sample methods. However, the decomposition is established for generic classification rather than document evidence, and the surface-indistinguishability phenomenon has not been measured for document extraction.

**Reference-free quality estimation and LLM uncertainty.**
Estimating output quality without a gold reference is well studied in machine translation, where reference-free quality estimation scores a hypothesis from the source alone (Rei et al., 2020, 2022); the same idea—judging an output's reliability without the answer—applies directly to document extraction. In the LLM setting, hallucination and error detectors such as semantic entropy (Kuhn et al., 2023; Farquhar et al., 2024), SelfCheckGPT (Manakul et al., 2023), and P(True) (Kadavath et al., 2022) flag likely-wrong outputs through repeated sampling or model self-evaluation.

Across these lines of work, error detection for document extraction is pursued either on fields or on tables, almost always with at least one additional LLM or VLM call, and without quantifying which errors are undetectable from the document itself. Our work targets this intersection. We verify both fields and tables with no additional LLM/VLM inference—scoring table structure directly from the extracted output and, optionally, cross-checking content against an independent OCR witness reused from the parse pipeline. We then specialize the selective-classification gap of Rabanser and Papernot (2025) to in-document evidence to measure which extraction errors are catchable and which are not—including the systematic case, noted but not analyzed by Jin et al. (2026), in which an extractor repeatedly returns the same wrong value that passes every channel. Our contribution is therefore an integration across granularities plus a document-specific detectability study, not a new confidence mechanism.

---

## Method

We refer to the system as **Evidence-Based Verification (EBV)**. EBV sits after an extraction pipeline and, for every value the pipeline returns, decides whether that value can be auto-accepted or should be sent to review. It reaches this decision using only evidence already present in the document and artifacts the pipeline has already produced, so it adds no further large-language-model (LLM) or vision-language-model (VLM) inference. EBV has a single decision contract (§Shared formulation), realized by three mode-specific verifiers—a spatial verifier for structured fields (§ROI), a signal verifier for unstructured and semi-structured fields (§Signal), and a structural verifier for tables (§Table-Trust)—and a common accept/route rule that composes them into a document-level decision (§Unified decision).

### Shared formulation

An extraction pipeline reads a document *d* and returns a set of extracted units *U(d)*. A unit *u* is either a **field** (a key–value pair, e.g. *Borrower Name → "Jane Doe"*) or a **table** (a grid of cells serialized as HTML). For each unit, EBV outputs a binary decision

> *a(u) ∈ {accept, route}*,

where **accept** means the extracted value is treated as correct and processed automatically with no human involvement—the "no-touch" outcome—and **route** means the value is sent to a reviewer (a human or a downstream check) because the available evidence does not support auto-acceptance. The document is accepted only when every one of its units is accepted:

> *A(d) = accept  iff  a(u) = accept for all u ∈ U(d)* ,

and otherwise routed. This conjunction reflects the operational reality that a single unverified value is enough to require a human to open the document.

Each unit is verified in one of three **modes**. Tables are always verified structurally. Fields are verified spatially when the document's type is a known structured (template-based) type, and by signals otherwise. The mode is selected from a flag supplied by the upstream pipeline, which marks whether the document type is structured; EBV performs no document classification of its own and treats both the document type and this flag as given inputs. Within a mode *m*, a unit is verified from in-document evidence *e_m(u)* by a mode-specific decision function *g_m*, and

> *a(u) = accept  iff  g_m(u)(e_m(u)) indicates trust* .

The three verifiers share this contract but differ in what evidence they read and how *g_m* is formed; the remainder of this section defines each one. Alongside the binary decision, every verifier records the individual evidence channels it computed (geometric overlaps, signal values, structural scores); the decision uses their calibrated aggregate, while the per-channel records are retained as the input to the detectability analysis of §[Analysis]. Algorithm 1 states the overall procedure; Figure 1 shows the shared pipeline with the three modes as branches.

> **Algorithm 1 — EBV document verification.**
> **Input:** document *d*; extracted units *U(d)*; upstream document type and structured-flag.
> **Output:** document decision *A(d)* and per-unit decisions *a(u)*.
>
> 1. for each unit *u ∈ U(d)*:
> 2. if *u* is a table: *a(u)* ← Table-Trust(*u*)  (§Table-Trust)
> 3. else if structured-flag(*d*): *a(u)* ← ROI(*u*)  (§ROI)
> 4. else: *a(u)* ← Signal(*u*)  (§Signal)
> 5. *A(d)* ← accept if *a(u)* = accept for all *u ∈ U(d)*, else route
> 6. return *A(d)*, {*a(u)*}

*(Figure 1 — placeholder: an overview diagram showing the extraction pipeline feeding EBV, the upstream structured-flag selecting the field mode, and the three verifiers emitting a common accept/route decision that is combined by the document-level conjunction. Caption to be written with the figure.)*

### Structured fields: spatial verification (ROI)

When a document is structured (i.e., it follows a fixed template layout), each field occupies a stable region of the page. The spatial verifier checks that an extracted value was read from the region where that field belongs. It works in two phases: an **offline** phase that learns, per field, where the field lives and how much deviation is tolerable, and an **online** phase that scores each new extraction against what was learned.

**Offline (learning).** From a set of labeled documents, the verifier learns three things for each field. First, it learns the field's **region of interest (ROI)**: for each document it forms the union of the word boxes that make up the field's value, removes cross-document outliers with a Tukey fence, and aggregates the surviving boxes into a single region by clipping each box edge to a lower/upper empirical-percentile range. Second, it **calibrates the field's decision rule**: the weights that combine the three spatial agreements (defined below) and the score threshold at which the field is accepted, chosen by a grid search over the labeled set to minimize verification errors. Third, it learns **context keywords**: the words that habitually surround the field and recur across most documents. The learned ROI, weights and threshold, and keywords are stored together as the field's profile.

**Online (inference).** Given a new extraction, the verifier maps the extracted value to its bounding box using the OCR tokens, disambiguating repeated values with the learned keywords. It computes three geometric agreements between this box and the ROI: **overlap** (intersection as a fraction of the value box), **center distance** (between the box centers, normalized by the ROI diagonal), and **intersection-over-union (IoU)**. These are combined into the field's **calibrated weighted vote**. When the field's learned keywords are strongly present around the value, the vote receives a bounded boost, so strong contextual support can carry a field whose geometry is marginal; a field whose value is legitimately empty is accepted when the field is habitually empty for its template (learned offline) or its context keywords are strongly present. The field is accepted when the (keyword-adjusted) vote clears its threshold, and routed otherwise.

### Unstructured and semi-structured fields: signal verification (Signal)

When a document has no fixed template, a field has no stable region to check against. The signal verifier instead reads the field name, the extracted value, and the document's page text, and asks whether the value is well-formed and genuinely supported by nearby text. Based on this evidence, it decides whether the value can be **accepted** or should be **routed** for review.

**Signals.** The verifier computes six deterministic signals from the field name, value, and page text, with no model call: (1) **format validity**—whether the value matches the expected form for the field type (date, amount, ZIP, state, and so on); (2) **keyword context**—whether the field name or its tokens appear in a text window around the value; (3) **source context**—whether the field's label sits on the same line as the value, within a few lines, or far away; (4) **value-in-text**—whether the value actually occurs in the document text; (5) **label–value distance**—the character distance between the nearest label and the value; and (6) **partial-extraction**—a penalty when a value appears to be a truncated fragment of a longer phrase. A weighted composite of these signals, averaged over the signals available for a given field, provides an interpretable trust score.

**Decision.** The signals, together with the derived danger signals and the emptiness prior, form a feature vector. Per document type, the verifier trains a small set of candidate tabular classifiers offline and selects the best-performing pair; at inference, this pair scores the feature vector, and the field is **accepted** only when both classifiers agree it is trustworthy, and **routed** for review otherwise.

**Safeguards.** Two deterministic adjustments sit on top of the classifier decision. First, **hard gates** override an accept to review when a disqualifying condition holds—a type mismatch, a value copied from an unrelated field, or an amount field left empty—and a hard cap correspondingly limits the interpretable trust score when such a danger signal fires. Second, an **empty-field prior**, learned per document-type and field from how often that field is genuinely blank in the reference data, promotes a *blank* extraction from review to accept when the field is habitually blank and no gate objects, so a correctly-empty field is not needlessly routed.

### Tables: structural verification (Table-Trust)

A table is extracted as an HTML grid of cells. The table verifier scores the table by asking two questions: whether the grid is internally coherent, and whether its text is faithful to what the page shows.

**Components.** The verifier evaluates a table on three core components—geometry, structural plausibility, and text conservation—plus a fourth, crop truncation; each produces a sub-score and flags the specific failures it detects. **Geometry** checks that the HTML grid is logically valid, flagging overlaps, holes, and impossible spans. **Structural plausibility** checks that the populated grid is reasonable—neither near-empty nor dominated by a single mega-cell, with sensible per-row fill and header-to-column counts—and flags defects such as over-segmented or phantom (blank) columns and cells placed in the wrong column. **Text conservation** compares the text in the HTML cells against an independent OCR reading of the table region—from a reader separate from the table extractor—measuring how faithfully the extracted text is preserved and flagging merged or dropped content; when no such reading is available, the table is scored on its structural components alone. **Crop truncation** flags content cut off at the image border. The trust score is a weighted average of the component scores, which are reported with their failure flags so that every decision is accompanied by its reasons.

**Decision.** A table is **accepted** when its trust score clears a calibrated threshold—selected on held-out data—and **routed** otherwise; the scorer itself only produces the score.

### Unified decision and cost

The three verifiers read different evidence—spatial geometry for structured fields, text signals for unstructured fields, and grid structure for tables—but each yields the same binary accept/route decision for the units it checks. A document is accepted only when all of its units are accepted; if any unit is routed, the document is routed for review.

A unit whose evidence is too thin to assess—for example a table with no OCR reading and an unparseable grid, or a non-empty field value that cannot be located in the document—lacks the support needed for acceptance and is therefore routed, not treated as a separate outcome.

Across all three modes the verification adds **no LLM or VLM inference**. The spatial verifier is deterministic geometry over OCR tokens already produced upstream; the signal verifier runs deterministic string and format checks scored by small tabular classifiers; and the table verifier runs deterministic structural checks together with an independent OCR reading, which it obtains by reusing the OCR already produced upstream by filtering the tokens that fall within the table region—rather than issuing a new recognition call. The only models invoked at decision time are these small, local tabular classifiers; the OCR reading is reused, not recomputed—so no new language- or vision-model call is made, the property the rest of the paper quantifies.