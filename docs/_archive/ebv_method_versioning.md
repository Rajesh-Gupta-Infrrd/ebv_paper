# Method — Version History & Decisions (traceability)

Tracks how the Method section evolved. The *finalized* prose lives in `ebv_paper.md`; this file keeps every version + the reasoning + the code facts it rests on, so nothing is lost.

---

## Draft v1 (current, in `ebv_paper.md`) — 2026-10-07

First prose draft. Structure:
1. **Umbrella + overview** — names the system **Evidence-Based Verification (EBV)**; one high-level paragraph with forward-references to the three modes + the shared decision.
2. **Shared formulation** — unit *u* (field|table); binary decision *a(u) ∈ {accept, route}*; document conjunction *A(d) = accept iff all units accept*; mode selection (table→Table-Trust; field→ROI if upstream structured-flag else Signal); shared contract *a(u)=accept iff g_m indicates trust*; note that per-channel evidence is logged for the §Analysis detectability study (not used by the rule). **Algorithm 1** (unified verify) + **Figure 1** placeholder (overview diagram, caption TBD).
3. **ROI (structured fields)** — offline: learn ROI (union box → 1.5×IQR Tukey → configurable percentile aggregation e.g. p5/p95), per-field pass-thresholds (percentile over matched items, capped), context keywords (left/top/bottom of label, majority recurrence). online: map value→bbox via OCR tokens (keyword-disambiguated duplicates) → overlap / center-distance / IoU → fixed weighted vote (0.50/0.30/0.20) ≥ fixed 0.70 → keyword-context adjustment (bounded boost; empty-field pass) → binary accept/route.
4. **Signal (unstructured/semi-structured fields)** — six deterministic signals (format_valid, keyword_context, source_context, value_in_text, label_value_distance, partial_extraction) with weights 0.20/0.20/0.15/0.15/0.20/0.10 (averaged over available) → interpretable composite; gates (force review) + hard cap + empty-field prior (accept habitual blanks); two tabular classifiers vote (both→NTP, neither→human-review, disagree→LLM-review); collapse NTP=accept, both reviews=route. Explicit: **no LLM/VLM**, routing by tabular classifiers.
5. **Table-Trust (tables)** — four components crop(20)/geometry(25)/structural(25)/text_conservation(25); weight-normalized average over active components; independent docTR OCR witness reused from parse pipeline (text_conservation = bag-of-tokens P/R/F1); defect detectors (column over-segmentation, phantom empty-column, position-misalignment+auto-alignment, concat-merge, missing-content); titles/captions excluded by region filter; 0–100 score, accept ≥85 (operating point, not a scorer constant).
6. **Unified decision + cost** — mapping table (native output → accept/route for all three modes); insufficient evidence → route; document conjunction; closing paragraph states the no-extra-LLM/VLM property (models invoked = tabular classifiers + reused OCR only).

---

## Draft v1.1 (user polish, 2026-10-08)

- **ROI opening reworded:** "When a document comes from a known template, each field occupies a stable region of the page." → **"When a document is structured (i.e., it follows a fixed template layout), each field occupies a stable region of the page."**
  - *Why:* "known template" blurred two things — the **document property** (structured/templatic = fixed layout, which is what *enables* spatial verification and what the upstream flag means) and the **operational requirement** (we must have *learned a profile* for that template). The opening should state only the property; the profiling requirement already lives in the offline paragraph. "structured" also keeps the opening consistent with the term used everywhere else in the Method. (User raised this; confirmed genuine, not bias.)
  - *Style:* used "(i.e., …)" rather than an em-dash gloss — the parenthetical "i.e.," form is the standard, more professional convention in ACL/NLP prose for a short in-line gloss.
  - *Honest caveat (not in the opening by design):* ROI in practice only works on templates profiled offline; that remains the offline phase's job to state, not the opening sentence's.

---

## Draft v1.2 (ROI structured section, user review, 2026-10-08)

Full rewrite of the ROI Offline/Online paragraphs after a detailed back-and-forth. Net changes:
- **Opening:** "When a document comes from a known template" was already → "When a document is structured (i.e., it follows a fixed template layout)" in v1.1; offline opener trimmed to "From a set of labeled documents" (dropped "of the template").
- **Numbers removed from Method body** (deferred to §Experimental Setup, per the hyperparameter-disclosure decision): Tukey "1.5 × IQR" → "a Tukey fence"; "5th/95th percentile" → "a lower/upper empirical-percentile range"; vote weights "0.50/0.30/0.20" and threshold "0.70" removed; grid steps omitted.
- **Keyword wording:** "surround the field's **label** (left/top/bottom, excluding value)…majority of documents" → **"surround the field and recur across most documents."** Chose **"field"** (not "value") on the user's point: the **empty-value** case has no value box, so keywords must anchor on the *field*; "field" covers both populated and empty cases and matches the code's label-anchored collection.
- **Offline decision rule — now states grid-search calibration** (see Flag 1 RETRACTION below): "learns per-field pass-thresholds (percentile)" → **"calibrates the field's decision rule: the weights that combine the three spatial agreements and the score threshold at which the field is accepted, chosen by a grid search over the labeled set to minimize verification errors."** (The Method states only the **generic** objective "minimize verification errors" — enough to avoid an objective-less grid search. The **internal lexicographic priority** — minimize FN → FP → maximize F1 — is **not disclosed**, and is kept out of §Experimental Setup too, per the user.) The **old percentile per-dimension pass-threshold method was dropped** from the paper at the user's instruction ("the threshold method is old; we used the weighted way for our results and production, so include weight calibration only").
- **Online tightened** (user: too verbose/tutorial-like, repetition): removed the "aligns…takes the union…" sub-clause (redundant with Offline union); "When a value occurs more than once, the learned context keywords disambiguate…" → "disambiguating repeated values with the learned keywords"; removed "pipeline's" from "OCR tokens" (pipeline under-introduced; reuse/no-extra-call is already stated in §Unified decision); removed the "weights/threshold are fixed defaults, while the ROI/pass-thresholds/keywords are learned" sentence (repeats Offline); list now introduced with a **colon + sentence split** (was clunky em-dashes).
- **Flow corrected (user caught a real bug in the prose):** v1 implied "reach a provisional decision → then the keyword check adjusts/re-applies," which misrepresents the code. The keyword boost is **part of forming the score**, not a second decision. Rewrote as a single flow: compute the three agreements → combine into the calibrated weighted vote → **if** learned keywords are strongly present, apply a bounded boost → test against the threshold **once** → accept/route. Empty value = the one special branch (decided on keywords alone).

---

## Draft v1.3 (Signal / unstructured section, user review, 2026-10-09)

Refined all four Signal paragraphs; user approved ("this version is really cool, just update exactly").
- **Para 1 (intro):** dropped the overstated example list ("free-form letters, identity and income documents, pay stubs and bank statements"); **removed the FALSE contrast** "unlike the spatial verifier it needs the document type" — the structured mode *also* needs doc type (to route + store/select the per-template profile), so doc-type is not a difference (user caught this). Replaced the offline/online sentence with a binary intro-closer: "Based on this evidence, it decides whether the value can be accepted or should be routed for review." Kept the user-approved "reads the field name… supported by nearby text" sentence verbatim.
- **Para 2 (Signals):** removed the explicit weights (0.20/0.20/0.15/0.15/0.20/0.10) → "averaged over the signals available," matching the ROI numbers-to-Setup rule. Six signal descriptions unchanged.
- **Para 3 (gates/caps/empty-prior):** unchanged (already binary-safe and code-accurate).
- **Para 4 (Decision) — rewritten for the real architecture + binary-only:** was "two small pre-trained tabular classifiers … NTP / human-review / LLM-check" (exposed the internal 3-tier). Now: "trains a small set of candidate tabular classifiers offline and selects the best-performing pair; at inference, this pair scores the feature vector, and the field is accepted only when both classifiers agree it is trustworthy, and routed otherwise." **3-tier kept internal** (accept iff both agree; disagree/both-reject both collapse to route — faithful binary). Preserves the no-LLM/VLM claim.

**Architecture verified (2026-10-08/09, code + Confluence):** per doc-type, **4** candidate tree classifiers trained (`run_ntp_direct_classifier.py:86,664-666,564-618` — RF, GBM, XGBoost, LightGBM; RandomizedSearchCV 50 iters, 5-fold, balanced_accuracy); selection picks best single model AND best pair over C(4,2)=6 pairs by error-catch-rate then NTP accuracy (`:849-872,1001-1035`); inference default 3-tier runs the selected **pair (2 models voting)** `_predict_field_3tier ntp_inference_engine.py:129-149`, single-model binary fallback when no pair. **No ensemble >2.** The "5" = a superseded Phase-3 experiment that included Logistic Regression (dropped). Confluence: built-system pages **"Unstructured NTP Inference — End-to-End Design"** (id 4607115287) and **"NTP for unstructured Documents using Scoring Mechanism"** (id 4498259972) MATCH the code; the earlier **"Proposed NTP Methods"** (4415553572) is a *superseded proposal* (confidence-scoring + LLM verification) — that is the "different architecture" the user remembered, NOT the built system.

**Deferred to §Experimental Setup:** the 4 algorithms (RF/GBM/XGBoost/LightGBM), the error-catch-rate selection metric + randomized search, and the single-classifier fallback.

**OPEN — signal-set verification (not yet run):** the trainer's default feature list names **7** signals including `ambiguity` and `source_phrase` (two the deterministic inference scorer dropped as LLM-dependent), while the inference scorer `ntp_scoring_pythonic.py` produces **6** deterministic signals (para 2's basis). Production trainer always runs `--auto-signals`, which almost certainly means it uses the scorer's 6 — but UNCONFIRMED. ⚠️ Must verify the exact training feature set before submission to keep the "six deterministic signals / no-LLM" claim airtight. User deferred the check.

---

## Draft v1.4 (structured empty-field correction, 2026-10-09)

- **ROI Online empty-field sentence corrected** (user approved option a): "a field whose value is legitimately empty is accepted on its keywords alone" → **"…accepted when the field is habitually empty for its template (learned offline) or its context keywords are strongly present."**
- *Why:* code check (`ntp_inference.py:1248-1258 final_pass_respecting_majority_empty`, called `:2251`; keyword empty-branch `:708-712`) shows the empty-field accept is a **DISJUNCTION**: accept if the offline **`majority_empty`** prior fires (`majority_empty = empties outnumber non-empties`, learned offline `ntp_pipeline.py:2704`, stored `:2779`) **OR** context-keyword match ratio ≥ 0.55. Geometry is skipped for empty values. So "keywords alone" was incomplete — the offline majority-empty prior is genuinely used (user was right they implemented it). 
- *Parallel for the paper:* structured now has a majority-empty prior and unstructured has its empty-field prior — both "accept habitual blanks." Note they are **separate subsystems** (ROI `majority_empty` boolean is inline in the empty decision; the classifier's `gt_empty_rate` prior is a post-decision override) — do not conflate.

---

## Draft v1.5 (Signal section reorder, user approved, 2026-10-09)

- **Reordered to signals → decision → safeguards** (was signals → gates/caps/empty-prior → decision), matching production order: the classifiers decide first, then post-decision overrides apply.
- **New Decision paragraph** (now before safeguards): classifiers (train candidate set → best pair → vote) → accept/route; clarified the weighted composite is an *interpretable trust value, not the decision rule*; kept the no-LLM/VLM line. Removed the trailing "a deterministic gate can still override" (moved to Safeguards).
- **New Safeguards paragraph** (now after decision): framed gates (+hard cap) and the empty-field prior as **post-decision adjustments** — gates demote accept→review; the empty-field prior promotes blank→accept. This matches production: classifiers → hard gates (`ntp_inference_engine.py:202-205`) → empty-prior override (`:209-216`), both post-decision; the empty-prior acts only on empty values.
- **Pair vs single:** kept the **pair** (3-tier default) per code + the DocuLab "Unstructured NTP Inference — End-to-End Design" (id 4607115287): `NTP_DEFAULT_MODE=3tier`, §3.6 two-model voting, §9 "3-tier via model pair." Single best model is only the binary fallback when `best_pair_config.json` is absent. (User still reviewing how the decision is made before final lock.)

---

## Draft v1.6 (Signal section polish, user approved, 2026-10-09)

- **Decision para — removed the redundant composite re-mention.** Dropped "The weighted composite of the signals serves as an interpretable trust value rather than the decision rule:" (the interpretable trust score is already introduced in §Signals and used by the hard cap in §Safeguards). Decision now ends: "The accept/route decision is made by the classifiers, and no LLM or VLM runs at this stage." (User declined the optional "not the composite score" clause — "interpretable" in Signals is sufficient signal.)
- **"Two safeguards" framing kept** (gates+cap = push-to-review; empty-prior = rescue-to-accept) over the older flat "three mechanisms" list — reads as deliberate design (reviewer + researcher view).
- **Pair + 6 signals confirmed by the team as production** — the text already matched (Decision uses the pair/both-agree; Signals lists six), so no change was needed.
- **Decision para trailing sentence deleted.** Dropped "The accept/route decision is made by the classifiers, and no LLM or VLM runs at this stage." — it repeated the classifiers (already named in the same sentence) and re-claimed no-LLM (already asserted at the system level in the overview + unified cost paragraph). "at this stage" also wrongly implied other stages use an LLM/VLM. Decision now ends cleanly at "…routed for review otherwise." No-LLM claim is unaffected (lives in the cost paragraph).

---

## Draft v1.7 (Tables / Table-Trust refinement, 2026-10-09)

Applied the same principles used on Structured/Signal (user asked me to refine proactively, then they'll do a manual pass).
- **Intro:** removed the trailing "It makes no LLM or VLM call; its only neural component is an optional, reused optical-character reading…" — consistent with dropping per-mode no-LLM re-claims (the property is asserted system-wide in the overview + §Unified decision; the OCR-reuse nuance remains in §Components text-conservation and the cost paragraph). Minor: "what the page actually shows" → "what the page shows."
- **Components — numbers removed** (→ Experimental Setup): dropped "(weight 25)×3 / (weight 20)"; replaced with the qualitative "three core components contribute in equal measure, with a fourth weighted lower and disabled by default." Trimmed "reporting how well the extracted text is preserved (precision, recall, F1)" → "measuring how faithfully the extracted text is preserved" (P/R/F1 metric detail → Setup). Kept the accurate mechanics: geometry, structural plausibility (+band/valley cross-check), text-conservation vs reused docTR witness, crop off-by-default but feeding structural; weight-normalized average over active components (witness-free still scored).
- **Defect detectors:** tightened the list (dropped repetitive "detector" after each), kept all five accurate detectors — column over-segmentation, phantom empty-columns, cell misalignment (incl. per-column alignment inference), concat-merge, missing content — plus the title/caption region-filter exclusion. (No dedicated dropped-row/title-drop detector, per earlier verification.)
- **Decision — number removed** (→ Setup): "accepted when its score is at least 85" → "accepted when the score clears a calibrated threshold—selected on held-out data"; kept "the scorer itself only produces the score" (honest: ≥85 is a production operating point, not a scorer constant; tables routing is our paper's binary framing). "0–100" stated once in the intro, not repeated in Decision.

**Deferred to §Experimental Setup:** the component weights (crop 20 / geometry 25 / structural 25 / text_conservation 25), the ≥85 accept threshold, and the P/R/F1 text-conservation metric.
**Note:** Tables section now awaits the user's manual review (same as Structured/Signal).

### v1.8 (Tables finalized after deep review, 2026-10-09)
Merged the old **Components** + **Defect detectors** paragraphs into one **"Components and failure flags"** paragraph, reworded Decision.
- **Folded the defect detectors into the components** (user: a separate "detectors" layer invites "what does the component do vs the detector?" overlap questions; and interpretability comes from components emitting score + flags, not a separate layer). Over-seg/phantom/misalignment → flagged by structural; merged/dropped → flagged by text conservation; overlaps/holes/impossible spans → flagged by geometry. Each component "produces a sub-score and flags the specific failures it detects."
- **Text conservation made generic** (user: don't tie the Method to our parse/extraction plumbing): "compares the text in the HTML cells against an **independent OCR reading of the table region**… flagging merged or dropped content; when no such reading is available, the table is scored on its structural components alone." Said **"OCR reading"** explicitly to kill the "re-extract the table?" misread. **Removed** tool names (docTR), the "parse pipeline's own OCR pass," "filtered to the table region," and the reuse clause — reuse/no-extra-pass stays in the system-level cost paragraph + Setup (user decided in-method reuse is deployment-specific and redundant with the cost paragraph).
- **Point 1 (weights framing) resolved:** dropped "**three contribute in equal measure, a fourth weighted lower**" → "three core components … plus a fourth, crop truncation." No equal/lower claim, no implied weight sum (the non-round 95 sum / normalization concern); all weights → Setup. Closing: "weighted average over the active components."
- **Interpretability framing (user's correction):** the system returns the weighted score **plus per-component sub-scores and flags** as the reasons — so we do NOT argue "named detectors beat an opaque score"; interpretability is inherent in the components' outputs.
- **Decision reworded:** dropped the redundant "The components and penalties combine into the trust score" (now in the Components paragraph) → "A table is accepted when its trust score clears a calibrated threshold—selected on held-out data—and routed otherwise; the scorer itself only produces the score."

**Deferred to §Experimental Setup:** component weights, the accept threshold, and the independent-OCR reading's provenance (reused upstream token-level reader; vision-based OCR is block-level only; no extra recognition pass).

### v2.0 (reviewer-agent pass, 2026-10-12)
Independent critical-reviewer agent read the current Method. Applied 2 of 3:
- **Fix 1 (real contradiction, Shared formulation):** "…these per-channel records are the input to the detectability analysis of §[Analysis] **and are not used by the accept/route rule itself**" → "…**the decision uses their calibrated aggregate, while the per-channel records are retained as the input to the detectability analysis**." (The channels ARE the decision inputs; the false "not used" clause removed. The disaggregated records are logged *additionally* for the analysis.)
- **Fix 2 (independence established, Table-Trust Components):** "an independent OCR reading of the table region" → "an independent OCR reading of the table region **—from a reader separate from the table extractor—**". One conceptual clause (not plumbing) so the independence that distinguishes us from Ajayi (who uses the extractor's own signals) is stated, not just asserted.
- **Fix 3 (insufficiency "by the same rule") — APPLIED:** "…—falls to *route* **by the same rule**, so insufficiency of evidence is handled as routing rather than as a separate outcome." → "…—**lacks the support needed for acceptance and is therefore routed, not treated as a separate outcome.**" Dropped "by the same rule" (implied a deterministic uniform route; true for tables/ROI but Signal routes softly via its classifier, not by a hard rule). New wording is honest for all three (acceptance needs support; thin evidence lacks it → route) and avoids a second "cannot" (the field example already has "cannot be located").
Reviewer confirmed fine: document-rule consistent across all 3 statements; mode selection consistent; no-LLM/VLM claim consistent and non-overclaiming; no gap-framing/results leakage in Method; altitude appropriate. Optional nitpicks (semi-structured routing, pair rationale, trust-score-cap clarity) also pending.

### v1.9e (cost paragraph — reading is core, upstream wording, 2026-10-12)
Replaced the cost paragraph (Variant A):
- **Independent OCR reading now presented as core, not optional:** "when available, reuses the pipeline's existing OCR as an independent reading" → "runs deterministic structural checks **together with** an independent OCR reading, which it obtains by reusing the OCR already produced upstream—**filtering the tokens that fall within the table region**—rather than issuing a new recognition call." (Matches the Tables section's core framing; fallback stays in the Tables section.)
- **Dropped "pipeline" references** → "**upstream**": spatial clause "OCR tokens the pipeline already produced" → "already produced upstream"; table clause "the pipeline's existing OCR" → "the OCR already produced upstream." (User: pipeline internals not disclosed anywhere.)
- **Closing:** "the OCR is reused from parsing rather than re-run" → "the OCR reading is reused, not recomputed—so no new language- or vision-model call is made."
- Note: M.0 overview still says "EBV sits after an extraction pipeline" (generic) — flagged to the user as a possible same-direction tweak, not yet changed.

### v1.9d (insufficiency example corrected, 2026-10-12)
- Insufficiency→route field example "**a field whose value cannot be located**" → "**a non-empty field value that cannot be located in the document**." *Why (user caught):* the old wording reads as the EMPTY case, which is wrong — empty fields are handled by dedicated logic that can **accept** them (ROI: majority-empty prior / keywords; Signal: empty-field prior), so "empty → route" would contradict the mode sections. The genuine insufficiency case is a **non-empty** value with no locatable/textual evidence → nothing to assess → route. Empty fields are explicitly *not* an insufficiency-route case.

### v1.9c (Unified-decision now states the document-level conclusion, 2026-10-12)
Keeping the section (user: it's needed) — its genuine job is to state the **document-level decision**, which v1.9b's lead didn't actually do (it only described per-unit decisions + "no reconciliation needed"). Verified the claim is correct (matches Algorithm 1 step 5 and the Shared-formulation formula `A(d)=accept iff all a(u)=accept, else route`), so option (b): state it in wording, no algorithm change.
- **First para** now: "…each yields the same binary accept/route decision for the units it checks. **A document is accepted only when all of its units are accepted; if any unit is routed, the document is routed for review.**" (document conclusion in words).
- **Insufficiency para:** dropped the redundant trailing "The per-unit decisions are then combined by the document-level conjunction of §Shared formulation" (now stated in the first para).
- Conjunction appears formally in Shared formulation and narratively here at the decision point (normal formal-then-narrative split). Section "Unified decision and cost" now genuinely delivers: document decision + insufficiency→route + cost. (Correcting my earlier over-swing to "remove the section.")

### v1.9b (Unified-decision premise fix — user caught, 2026-10-12)
**Deeper issue the v1.9 pass missed:** once each mode section presents a clean binary accept/route, the Unified-decision section's premise—"the three verifiers emit decisions of *different native shapes* … mapped onto a common contract"—is no longer true. We unified the output shape *at the source*, so there is nothing to map; the lead + mapping table merely restated the sections. **Fix:** removed the "different native shapes" lead and the entire mapping table; replaced with one sentence — "Although the three verifiers read different **evidence**—spatial geometry / text signals / grid structure—each produces the same binary accept/route decision **directly, so no cross-mode reconciliation is needed**." (Different evidence, same decision — unification stated honestly, no fictitious mapping step.) Insufficiency→route note and the cost paragraph unchanged. (Lesson: fixing table *cell contents* in v1.9 without re-examining whether the table should exist.)

### v1.9 (M.0 / Unified-decision consistency pass, 2026-10-12)
End-to-end review found the overview/unified sections were written pre-refinement and out of sync with the finalized modes. Fixed 5:
1. **Unified table — Table-Trust row**: "trust score in [0,100] | score ≥ 85 | score < 85" → "trust score | clears calibrated threshold | below threshold" (matches the finalized Tables section; 0–100 and 85 stay in Setup).
2. **Unified table + lead — Signal 3-tier hidden**: lead "the signal verifier a three-way routing outcome" → "a classifier-agreement decision"; table row "NTP / LLM-review / human-review | NTP | LLM-review or human-review" → "classifier-pair agreement | both agree trustworthy | otherwise" (keeps the 3-tier internal, consistent with the Signal section).
3. **"witness" → "OCR reading"** terminology aligned (unified-decision insufficiency clause + cost paragraph).
4. **Cost sentence reframed** (the OCR-is-a-vision-model trap): "…the reused OCR, none of which is an additional generative or vision model at decision time" → "The only models invoked at decision time are these small, local tabular classifiers, and the OCR is reused from parsing rather than re-run—so no new language- or vision-model call is made." Claim now rests on *no new call* (reuse), never on "OCR isn't a vision model." Matches the title ("Language- or Vision-Model Calls").
5. **Shared formulation, route definition**: "(a human, or a downstream LLM check)" → "(a human or a downstream check)" — stops half-exposing the internal LLM-review tier.

Still-open placeholders (not errors): Figure 1 to be drawn; §[Analysis] cross-ref label to finalize.

### v1.8a (Tables polish, user approved, 2026-10-12)
- **Heading** "Components and failure flags." → **"Components."** (flags are described in the body; lead-in kept short).
- **Crop sentence** → straightforward: "**Crop truncation** flags content cut off at the image border." Dropped "disabled by default" (operating-point → Setup) and the "band/valley still feed structural plausibility" plumbing (→ Setup). *Setup to-do:* note crop is off by default (weight 0).
- **Closing sentence** reworded for clarity/professionalism: "The trust score is the weighted average over the **active components**, and the **per-component sub-scores** and flags accompany it…" → "The trust score is **a weighted average of the component scores, which are reported with their failure flags so that every decision is accompanied by its reasons.**" Dropped the "active components" jargon (witness-absent case already handled in the text-conservation sentence) and simplified the interpretability clause.

### v1.7b (user review, 2026-10-09)
- **Table intro reworded** → "A table is extracted as an HTML grid of cells. The table verifier scores the table by asking two questions: whether the grid is internally coherent, and whether its text is faithful to what the page shows." Dropped the redundant/premature "scoring … from structural evidence and an independent reading of the same region" (it repeated the two dimensions already stated and previewed the witness as jargon before Components defines it, and implied the optional witness is always used). Fixed "structure/grid" slash → "grid."
- **"two questions" framing confirmed OK with current flow** — research papers don't require a rigid Q1/Q2 section split; the body addresses both (structural components → coherence; text conservation → faithfulness).
- **OPEN:** "0–100" is now absent from the whole Tables section (removed from Decision earlier, now from intro). Pending user choice: (a) restore it once in the Components trust-score sentence, or (b) leave it out entirely.

### v1.7a (user review, 2026-10-09)
- **Removed the titles/captions region-filter sentence** ("Text outside the table region, such as titles and captions, is excluded by the region filter so it is not mistaken for dropped content.") from the Defect-detectors paragraph. *Why (user):* it exposes an **internal, MinerU-OCR-specific defensive measure**, not a general method property — it reads like airing an edge-case flaw and should not be in the paper. Principle to carry forward: **do not expose internal/tool-specific defensive handling or flaws** in the Method. (The `majority_empty`/region-filter type of implementation detail stays internal.) The "no dedicated dropped-row/title-drop detector" note was only in the explanation, never in the paper.

---

## Decisions & reasoning (why it reads this way)

1. **One umbrella name + one decision contract, three modes as specializations.** Per ACL Method-writing convention (rational reconstruction): shared notation (*u*, *a(u)*, *g_m*), one shared accept/route rule stated once, modes presented as branches of it, one overview figure, one algorithm box. Goal: three systems read as **one unified method**, which is exactly the framing the user asked for ("we are saying this as a unified system").
2. **Binary accept/route, not 3-tier, not the 3-state evidence abstraction.** User decision: unify on binary. Each mode's native output is *mapped* to binary in the §Unified-decision table; the Signal mode's native 3-tier (NTP/LLM-review/human-review) is collapsed (NTP=accept, both reviews=route), which the code's own binary mode does identically. Dropped the earlier corroborated/contradicted/insufficient 3-state framing — "insufficient" is folded in as "→ route."
3. **"accept" defined explicitly** = auto-accept the extraction as correct, no human review (the no-touch outcome); "route" = send to a reviewer. Fixes the user's "what is accept?" question.
4. **Routing framed honestly as an upstream flag.** The verifier receives a `structured` flag (set upstream from the document type) and does no classification itself; doc-type and the flag are given inputs. Pre-empts the reviewer's "how do you get the doc type / isn't this non-adaptive?" without claiming a router we don't have. (Dependency on the upstream classifier to be acknowledged in Limitations.)
5. **NO "however"/gap/comparison sentences in Method** (fixes the Related-Work-era mistake). Every design choice is motivated by the *property we want* (stable region, faithful text, no extra call), never by attacking a named prior system. Comparison stays in Intro/Related Work.
6. **Present tense for what the method does; no results/scores/"best" claims.** The detectability study is only forward-referenced (§Analysis); no numbers in Method. Per ARR guidance (no method/results conflation, no over-claiming).
7. **Cost claim stated precisely at the end** — "no LLM or VLM inference"; the only models are lightweight tabular classifiers (Signal) + reused docTR OCR (Table witness). Never says "no model."

---

## Code facts this draft rests on (verified 2026-10-07 by five parallel reads; file:line)

### ROI / structured fields — `/Users/rajeshgupta/Git_Clones/dociq` (branch feature-MPS-2382)
- Union box per doc `compute_union_bbox` `ntp_pipeline.py:2626-2665`; aggregated across docs; IQR 1.5×Tukey `_filter_outliers_iqr:2667-2673` (len≥4) on center/width/height.
- **ROI method is configurable** `self._roi_method:2383`; `percentile_5_95:2721-2725` (on RAW start/end, not IQR-filtered); also percentile_20_80 / mean_2std / mean_only. → paper says "configurable percentile aggregation, e.g. p5/p95" (not hardcoded).
- Per-field pass-thresholds learned `_compute_threshold_scores:2809-2883` (only on value-matched items; percentile stat default p5/p95; capped overlap/IoU≤90, center≤0.2); stored in `roi["statistics"]`.
- **Weighted-vote weights + score threshold ARE calibrated per field by grid search** (CORRECTED 2026-10-08 — see Flag 1 retraction): `RoiWeightedVotingCalibrationEngine ntp_pipeline.py:3042-3497` searches (overlap, center, iou) weight triplets (sum=1) × a threshold grid, scoring the golden set by a lexicographic objective (minimize FN → FP → maximize F1), **per field** (`calibrate_all_fields_from_samples:3378-3392`), and **writes** `extractedWeightedVotingWeights`/`extractedWeightedVotingScoreThreshold` into the field ROI statistics (`:3402,3407`). Wired into the orchestrator (`:4569,4698-4708,2467-2479,2582-2634`) and **enabled in the production bugbuster service** (`ntp_pipeline_service.py:49 weight_calibration={"enabled": True}`). The literals `0.50/0.30/0.20` + `0.70` (`DEFAULT_EVAL_CONFIG ntp_inference.py:1358-1363`) are **fallback defaults** used only when calibration is off or a field has no samples; read sites `ntp_inference.py:770,781`, `ntp_pipeline.py:4035,4047`. (Earlier reader missed the writer: it builds the keys via an f-string prefix and the grid via `np.arange`, so literal-string and `itertools.product` greps both missed it.)
- **Per-dimension percentile pass-thresholds** (`_compute_threshold_scores:2809-2883`, overlap/center/IoU thresholds from matched items, capped) are the **OLD/alternative "all-three-AND" method** — learned but NOT the production decision driver. **Dropped from the paper** at user instruction (weighted grid-search way only).
- Context keywords learned `aggregate_context_keywords_from_golden ntp_pipeline.py:1881-1968` (left/top/bottom neighbors, exclude value/right; ≥0.6 doc fraction core; cap 20); stored `roi["statistics"]["contextKeywords"]:2429-2430`. (User's memory that they implemented keyword matching = CONFIRMED.)
- Online map value→bbox via OCR: `FieldMapper.enrich_fields` over Mongo OCR tokens `ntp_inference.py:2032,2055,2066-2069`; value bbox `compute_union_bbox:2154-2158`.
- Three signals: `calculate_center_distance:938-945` (normalized by ROI diagonal), `calculate_overlap_percentage:948-961` (inter / extracted-box area), `calculate_iou_percentage:964-977`. `evaluate_bbox_against_roi:1270-1337` (weighted vote vs 0.70; else AND-of-three). (Function's own fallback thr 0.535, but runtime config passes 0.70.)
- Keyword-context decision `apply_keyword_context_decision:667-680` (called `2265-2281`): merge value box+ROI, nearby OCR tokens, match ratio; empty-field pass if ratio≥0.55; weighted boost up to +0.12 if ratio≥0.35; threshold-mode OR rule.
- Binary per field `final_label = ntp|non_ntp:2283`; doc ntp iff all fields ntp `2347-2364`. v2 router maps ntp→0.98, non_ntp→human_review 0.55 `ntp_inference_v2.py:19-37`.
- **Routing = boolean `req.structured`** `ntp_inference_v2.py:64`, schema `ntp_inference_v2.py:31` (true→ROI, false→classifier). doc_type carried but NOT the branch decision. **No `isStructuredDocType()` function** — only a Mongo data field used at training `bugbuster_job_runner.py:318-334`. ⚠️ See Flag 2.

### Signal / unstructured fields — same repo, `app/ntp_classifier_inference/`
- Six signals + impls in `ntp_scoring_pythonic.py`: format_valid(`242-311`), keyword_context(`344-390`), source_context(`397-467`), value_in_text(`520-527`), label_value_distance(`604-634`), partial_extraction(`641-665`). Two legacy LLM signals (ambiguity, source_phrase) DROPPED (docstring 20-22).
- `DEFAULT_WEIGHTS:32-39` = 0.20/0.20/0.15/0.15/0.20/0.10; weighted avg renormalized over available (non-None) signals `776-785`.
- Gates/caps: boolean/signature soft cap 0.6 `787-790`; HARD_SIGNAL_SCORE_CAP 0.45 `64`, `_apply_hard_signal_caps:948-961` (type_mismatch / cross_field_copy / optional_borrower_consistency); decision gates flip NTP→HUMAN_REVIEW `ntp_inference_engine.py:202-205` (reasons incl. name_holds_zip, empty_amount_or_fee).
- Empty-field prior `empty_field_prior.py` — per (doc_type, field) GT empty rate `build_gt_empty_prior:55-83`; promotes review→NTP for habitual blanks `apply_empty_prior_override:144-175` (rate≥0.50, n≥20, no blocking gate; empty_amount_or_fee overridable).
- Decision = **two tabular classifiers** `_predict_field_3tier ntp_inference_engine.py:129-149` (both 1→NTP; both 0→HUMAN_REVIEW; disagree→LLM_REVIEW), features = signal dict (joblib/scikit/LightGBM, NOT neural, NOT LLM). `final_score` NOT a model feature. Doc roll-up `234-242`. Binary mode emits NTP/REVIEW `200` (= our collapse).
- Inputs `predict_document:151-157` = ner_output + text + doc_type + mode; **doc_type IS used** (per-doctype model selection + prior), not inside the six raw signals.
- Text = raw page text from storage `document_text_builder.py:38-61` (⚠️ not provably OCR vs digital layer — paper says "page text from the pipeline").
- **No LLM/VLM/transformer/API client anywhere** in the four files (imports: json, pathlib, joblib, numpy, pandas). ⚠️ but tabular ML models ARE invoked — do NOT say "no model."

### Table-Trust / tables — `/Users/rajeshgupta/Projects/DocAI`, `scripts/extract/table_extraction/`
- `DEFAULT_WEIGHTS scoring.py:44-52` = crop 20 / geometry 25 / **structural** 25 / **text_conservation** 25 (+ reading_order 0 / token_shape 0 advisory). CORE_SIGNALS `:56`.
- **crop zeroed unless `use_crop_signal=True` (defaults False)** `:855,877-878,928-931`; its band/valley estimates still feed structural `:884-886,914-921`. → live core usually geometry/structural/text_conservation.
- geometry = HTML grid validity `score_geometry:914`; structural = plausibility (+band/valley) `score_structural_plausibility:915-921`; text_conservation = bag-of-tokens P/R/F1 vs witness `analyze_text_conservation:933-935`.
- Independent witness: order = caller tokens → **reused pipeline docTR tokens** (`tokens_from_ocr_result`, source `doctr_parse_tokens`) → docTR-on-crop only if `run_doctr_if_needed=True` `:888-905`; witness independent of extractor (same-engine fallbacks weak last resort). docTR = pretrained neural OCR `content_conservation_signals.py:137-163`. **No LLM/VLM** (repo-wide grep clean).
- Weight-normalized average over used signals `:1077-1082`; boosts/penalties `:1116-1164`.
- Three structural defect detectors: column over-segmentation (`TOKEN_COL_OVERSEG`), phantom empty-column (`count_phantom_empty_cols:950`), position-misalignment (`count_position_misalign:951-953`, incl. auto-alignment edge-anchor + decisiveness guard). Reading-displacement detector OFF by default. Plus text-module detectors: concat-merge (`count_concat_suspects_v2`), missing-content (`count_missing_content`) `:940-946`.
- **No dedicated dropped-row/col or title/caption-drop detector** — bands/valleys mismatch + missing_content + region bbox-filter cover these (`:861-866`). CORRECTION folded in.
- Score 0–100 `base_trust_score:1179`; **≥85 accept is a documented production operating point** (`Table_Trust_Scoring.md:24-27,98,474`; harness sweep [50,60,65,75,85] `evaluate_rdbench_trust.py:125`), **scorer itself is threshold-free**. "NTP/route" is OUR paper's terminology; tables routing not implemented in that repo (`evaluate_rdbench_trust.py:4`).

### Confluence "Proposed NTP Methods" (page 4415553572)
- Entirely **proposals**, LLM-centric (ROI with document-registration/anchoring for skew, OCR↔LLM fuzzy normalization, IoU≥70%; a 5-signal 0–1 structural-confidence pre-filter with 0.90/0.50 thresholds; filtered-context LLM verification). **No built no-LLM system, no signal-classifier, no VLM, no explicit router** documented there. → Method written from CODE, not this page. Useful only as cross-check that the ROI *concept* matches.

---

## ⚠️ Honesty flags raised to the user before writing (2026-10-07)
- **Flag 1 — RETRACTED (2026-10-08). The ROI weights ARE learned; my earlier claim was wrong.** I had written that the vote weights/threshold were fixed defaults with no learner. A targeted re-check found `RoiWeightedVotingCalibrationEngine` (`ntp_pipeline.py:3042-3497`), a per-field grid-search calibrator that writes `extractedWeightedVotingWeights`/`extractedWeightedVotingScoreThreshold` and is **enabled in production**. The user's memory was correct. Paper now states the weights + threshold are **calibrated offline, per field, by grid search on the labeled set** (minimize FN → FP → F1); `0.50/0.30/0.20`+`0.70` are fallback defaults only. Lesson: a missing identifier from a grep is not proof of absence when keys are built via f-strings.
- **Flag 2 — routing is an upstream boolean flag**, not a doc-type lookup inside the verifier, and `isStructuredDocType` is a data field, not a function. Resolution: framed as "upstream-provided structured-flag (derived from document type) selects the mode; verifier does no classification." Consistent with our agreed "mode by doc type from upstream" story. **Awaiting user reaction.**

## Writing conventions applied (from the Method-writing research)
- Overview paragraph + forward refs; task formalized before components; notation defined at first use and reused across modes; data-flow order; present tense; active "we" with varied subjects; **no gap/"however"/comparison sentences**; design choices motivated by the property wanted; no results/scores/"best"; Algorithm box + Figure placeholder with self-contained caption to follow; every symbol/equation glossed in plain words.

## Open items / to confirm with user
- Flags 1 & 2 above (factual framing) — confirm or adjust.
- Whether to self-cite our own prior Table-Trust as related work (anonymized) — still open from Related Work.
- Figure 1 — needs to be drawn; caption to be written with it.
- Decide final home of the "insufficient evidence → route" sentence (Method vs Formulation section, once Problem/Formulation is written — may move there).
- `[Analysis]` cross-reference label to be finalized once section numbering exists.
- Confirm umbrella name "Evidence-Based Verification (EBV)" is acceptable for the double-blind submission (not identifying).
