# EBV Paper — Related Work v2 (post full-text debate, moderated)

**Date:** 2026-10-05 · **Supersedes:** `…_related_work.md` (v1)
**Method:** two full-text reviewer-persona passes (Researcher + adversarial Reviewer), moderated by the lead (disputes adjudicated against the source papers).
**Status:** ⚠️ **Read §0 first — the honest verdict changed the paper's tier.**

---

## 0. Moderated verdict (the headline)

After full reads, **the "three firsts" framing does not survive.** The defensible paper is an **integration + floor-characterization** contribution, honestly framed — realistically a **workshop / short / Findings** paper, not a top-main-track "novel system."

**The two disputed facts (agents disagreed; moderator adjudicated against the sources):**

| Disputed claim | Researcher | Reviewer | **Moderator ruling** |
|---|---|---|---|
| "All document competitors spend ≥1 extra model call" | True | **False** | **Reviewer right.** ConfBench (2608.01792) has a zero-extra-call logprob mode; Ajayi (2507.02009) flags from existing outputs. **Soften to a conjunction**, not a blanket comparative. |
| Does Ajayi (2507.02009) use our *independent second-OCR witness* for tables? | **No — it aggregates the pipeline's own TSR+OCR confidences** | Yes (independent PaddleOCR witness) | **Researcher right (abstract: "aggregate the uncertainties introduced by TSR and OCR").** Our independent-witness check is a *genuine but narrow* differentiator. ⚠️ **Verify from Ajayi's full PDF — it decides whether our table mechanism is novel.** |

**Claim-by-claim honesty (final):**
- ❌ *"first zero-extra-call"* — false comparative (ConfBench, Ajayi).
- ❌ *"first document detectability floor"* — overclaimed **and mis-anchored**. Rabanser (2510.20242) is the selective-classification **gap**, not a "detectability frontier." Real floor precedents: **2608.23663** (reference-free frontier, LLM-QA) + **2608.14639** (document-level PAC/certifiability floor). **Drop "first"; re-anchor the lineage.**
- ⚠️ *"fields AND tables"* — literally true, but each half is largely prior art (fields: 2609.20110 etc.; tables: 2507.02009). The **union is an integration**, not an invention.
- ✅ **What survives:** a **unified, zero-extra-neural-inference, independent-witness** detector across **fields + tables**, plus an explicit **characterization of which document errors are undetectable from in-document evidence** — especially the **systematic-confident-wrong case** (identical wrong value passes every channel check), which 2609.20110 flags but no one measures for documents.

**Honest positioning (use this exact framing):** *"No prior work unifies zero-extra-neural-inference error detection across fields and tables, with an independent-witness check, and characterizes the in-document detectability floor for systematic confident errors."* — a **packaging + analysis** gap, not a conceptual void.

---

## 1. Verified paper inventory (full-text, both agents agree these exist)

Confirmed titles (correct any working labels):
- **2510.20242** — Rabanser & Papernot, *What Does It Take to Build a Performant Selective Classifier?* (NeurIPS 2025). **General ML; the selective-classification *gap* decomposition (Bayes/approx/rank/stat/misc). Not documents.**
- **2609.20110** — Jin et al., *Perception, Layout, and Validation: Calibrated Confidence for Reliable STP of Financial Documents* (Sep 2026). **The near-twin for our structured-fields channel.**
- **2606.24420** — Kumar (Perfios), *Beyond Logprobs: Multi-Signal Confidence Engine (ExtractConf).* Dual-call Hunter+Mapper (2 LLM calls), fields.
- **2608.01792** — AWS, *Can You Trust the Confidence? ConfBench.* KIE calibration **benchmark**; has a **zero-extra-call logprob mode**; fields; no ceiling.
- **2604.23644** — Jha, *RaV-IDP: Reconstruction-as-Validation.* Tables+text+images, but **GPT-4.1 vision fallback** (extra call).
- **2608.14639** — Gurram (Zasti AI), *Valid Per-Field Selective Risk Control for Document Extraction.* Post-hoc per-field accept/review, PAC certificates; **document-level floor** (near-vacuous certification in 19/40 splits; label-noise floor). Headline signals use k=3 self-consistency.
- **2608.23663** — Pandey et al., *Confidently Wrong, Silently So.* **Explicit measured detectability frontier** (surface-indistinguishability, AUROC≈0.55; O(1)-fails/O(N)-works cost ladder). On-device **LLM QA/summarization — not documents**.
- **2206.02628** — Nguyen et al. (Cinnamon AI), *HYCEDIS* (KDD DI 2021). Hybrid conformal confidence engine tied to one IE stack; fields; needs GT to train.
- **2604.25855** — Rodriguez & Rohrbach, *SIEVES.* Selective prediction via visual evidence scoring — **VQA, not documents**.
- **2507.02009** — Ajayi, He, Wu, *Uncertainty-Aware Complex Scientific Table Data Extraction* (Jul 2025). **Conformal UQ aggregating the pipeline's own TSR+OCR confidences** (not an independent witness); scientific tables; "verify 47% → +30% quality."
- **2608.09842** — *From Diagnosis to Correction* (DEC). Table error diagnosis + **agentic VLM correction** (multi-call).

---

## 2. Per-competitor differentiator (corrected, honest)

- **2609.20110 (P/L/V):** near-twin for structured fields (signals→fuse→conformal route). Ours: **non-vision, zero extra call**, adds **tables**, and **measures the floor** (incl. the systematic-confident-wrong case it only *flags*). *Concede the fuse/route concept.*
- **2606.24420 (ExtractConf):** 2 LLM calls, fields. Ours: zero extra call; fields+tables.
- **2608.01792 (ConfBench):** a **benchmark** (not a method); has a zero-call logprob mode; fields; **built on RealKIE-FCC** (⚠️ our unstructured dataset — differentiate on *task*, not dataset). Ours: a *method* + floor + tables.
- **2604.23644 (RaV-IDP):** cross-granularity but via reconstruction + **vision-LLM fallback**. Ours: cross-granularity with **no verifier call**, and measures catchability rather than gating.
- **2510.20242 (Rabanser):** general-ML selective-classification **gap**. Ours: **adapt** its decomposition to in-document evidence (cite as method, **not** as "frontier").
- **2608.14639 (Per-Field Risk Control):** conformal **validity**, fields, k=3 self-consistency. Ours: zero extra call, cross-granularity; **and this is a document floor precedent — cite it for the floor, don't claim "first."**
- **2608.23663 (Confidently Wrong):** the **measurement method** for a reference-free floor, but **LLM-QA**. Ours: brings that method to **document extraction** with in-document evidence, no extra calls. *This is our true floor-lineage anchor.*
- **2206.02628 (HYCEDIS):** stack-specific conformal confidence, fields, needs GT. Ours: architecture-agnostic over outputs; adds floor + tables.
- **2604.25855 (SIEVES):** selector on observable evidence, **VQA**. Cite as the "selector on observable outputs" precedent.
- **2507.02009 (Ajayi):** **aggregates the pipeline's own TSR+OCR uncertainties** (conformal), reference-free, likely zero extra call, scientific tables. Ours differs **only** by using a **separate independent OCR witness** (cross-check) rather than self-confidence aggregation. ⚠️ **the narrowest, most important differentiator — verify the full PDF.**
- **2608.09842 (DEC):** table **correction** via agentic VLM controller (multi-call). Ours: **detection** at zero cost.

---

## 3. Chronological lineage (most-recent → oldest)

Tags: **(a)** NTP/STP auto-accept for docs · **(b)** extraction confidence/verification (KIE & tables) · **(c)** methodological ancestors.

1. **2609.20110** P/L/V STP (Sep 2026) **(a)(b)** — SOTA signals→fuse→conformal-route for auto-approval. *Nearest edge of the gap.*
2. **2608.14639** Per-Field Selective Risk Control (Aug 2026) **(b)(c)** — conformal PAC validity; **document-level floor**.
3. **2608.23663** Confidently Wrong, Silently So (Aug 2026) **(c)** — first clean reference-free **floor measurement** (off-domain LLM-QA).
4. **2608.09842** Table Diagnosis→Correction (Aug 2026) **(b)** — table failure taxonomy + agentic correction.
5. **2608.01792** ConfBench (Aug 2026) **(b)** — KIE confidence **benchmark**.
6. **2606.24420** ExtractConf (Jun 2026) **(b)** — document signals beat logprobs (2 calls).
7. **2604.23644** RaV-IDP (Apr 2026) **(b)** — reconstruction-as-validation across entity types (VLM fallback).
8. **2604.25855** SIEVES (Apr 2026) **(b)(c)** — evidence-scored selective prediction (VQA).
9. **2510.20242** Rabanser & Papernot (NeurIPS 2025) **(c)** — selective-classification **gap**/oracle decomposition (general ML).
10. **2507.02009** Uncertainty-Aware Table Extraction (Jul 2025) **(b)** — conformal UQ over internal TSR+OCR confidences (no independent witness).
11. **2206.02628** HYCEDIS (2022) **(b)** — foundational document-IE hybrid confidence engine.

**Foundational anchors (year + role only):** selective prediction — El-Yaniv & Wiener 2010; SelectiveNet 2019 (1901.09192); AURC/E-AURC 2019 (1805.08206). Conformal — Angelopoulos & Bates 2021 (2107.07511); Conformal Risk Control 2022 (2208.02814); Learn-Then-Test (2110.01052). Reference-free QE — COMET-QE/CometKiwi (Rei 2020/2022) *(note: we are NOT GT-free — we use learned offline references)*. LLM uncertainty — Semantic Entropy (2302.09664 / Nature 2024); SelfCheckGPT (2303.08896); P(True) (2207.05221) *(all multi-call — the cost axis we remove)*. Fact verification — FEVER 2018; AIS 2023; RARR 2023. Table/doc eval — TEDS (1911.10683); GriTS (2203.12555); VRDU (2211.15421); DocILE (2302.05658).

---

## 4. Ordered Related-Work plan (exact presentation order)

**§A — Confidence & selective acceptance for document KIE (the direct line), oldest→newest to show escalation:** HYCEDIS → ExtractConf → ConfBench → Per-Field Risk Control → **P/L/V (near-twin, land the shared verdict: fields-only / mostly extra-call / no document floor).**
**§B — Verification across granularities & for tables:** RaV-IDP → Ajayi 2507.02009 → DEC 2608.09842. *(Motivates our topology + independent-OCR-witness design; explicitly contrast Ajayi: self-confidence aggregation vs. our independent witness.)*
**§C — Selective prediction with evidence scoring + the floor phenomenon:** SIEVES → **Confidently Wrong (2608.23663) — our floor-method anchor.**
**§D — Theoretical frame:** selective-prediction anchors (El-Yaniv/Wiener; SelectiveNet; AURC) → conformal risk control → **Rabanser (2510.20242) — the gap decomposition we *adapt* (not a "frontier").**
**Positioning paragraph (after §D):** name the packaging+analysis gap (zero-extra-neural-inference × fields+tables × independent-witness × in-document floor for systematic confident errors) + the channel-complementarity finding.

---

## 5. Honest, defensible contribution claims (narrowed)

1. **A unified, zero-extra-neural-inference, architecture-agnostic detector across fields *and* tables** (structured ROI + unstructured non-vision/non-LLM signals, doc-type routed; tables via topology + an **independent OCR witness**). *Claim: unification at no extra model call — not "first cheap detection."*
2. **Characterization of the in-document detectability floor** — which extraction errors are catchable vs. undetectable from in-document evidence — following the surface-indistinguishability/cost-ladder method of **2608.23663** and adapting the gap decomposition of **2510.20242**; with special attention to the **systematic-confident-wrong** case (flagged but unmeasured by 2609.20110). *Claim: first such characterization for document extraction — not "first floor."*
3. **Channel complementarity** across heterogeneous evidence (ROI/region, text-structure signals, independent witness) — empirically, which channels catch which error populations.
4. *(Supporting engineering, not headline):* the specific zero-call, non-vision instantiation + structured/unstructured routing.

---

## 6. Honesty constraints (hold in the writing)
- **Drop "first" and "all competitors spend ≥1 call."**
- **Re-anchor the floor** to 2608.23663 + 2608.14639; present Rabanser as a gap decomposition we adapt.
- **Fields fuse/route concept is occupied (2609.20110)** → claim the zero-call/non-vision instantiation + floor, not the idea.
- **Not GT-free** (learned offline references) — do not borrow RaV-IDP's "label-free" claim.
- **RealKIE overlap** with ConfBench — differentiate on task.
- **Channels aren't individually new** — claim the *unification + floor characterization*.

## 7. Verification to-do (before citing)
- [x] **Ajayi 2507.02009 — RESOLVED (full method read):** it **aggregates the pipeline's own TSR+OCR confidences** (conformal), zero extra call, scientific tables; **no independent second OCR.** → our multi-signal table scorer differs (see §9).
- [ ] 2608.14639 — confirm the document-level floor framing we cite.
- [ ] 2608.23663 — confirm the surface-indistinguishability method we anchor the floor to.
- [ ] Re-confirm 2608.09842 scope; MSCE (ResearchSquare) + IJDAR (10.1007/s10032-026-00572-y) metadata.

## 8. Bottom line
Honest related-work coverage and lineage are now solid. The **novelty is an integration + a document floor *characterization*, not three firsts.** Viable as a **workshop/short/Findings** paper with the framing above; as a top-main-track "novel system," it is oversold. **Decide the target tier before writing** — that choice sets how hard the novelty claims can be pushed.

---

## 9. Updates since v2 drafted — deep re-checks + head-to-head plan (2026-10-05)

**P/L/V (2609.20110) — deep re-read:**
- **Fields/key-value only — tables explicitly out of scope.** (So it does *not* touch our tables side.)
- **No document-type routing.**
- **Needs VLM calls:** perception = VLM verbalized confidence; validation = agreement between **two** VLMs (dual-VLM extraction, keep the higher-scored). → genuinely expensive.
- **Names but does not measure the systematic-error floor:** *"blind to systematic errors, where the same wrong value is returned every time."* → the near-twin flags our gap and leaves it unmeasured.
- **Used FATURA + DocILE + VRDU** → **FATURA is shared with us** (the head-to-head set).
- **Our fields channels overlap theirs:** our ROI ≈ their *layout* channel (per-field position prior); our non-vision signals ≈ their *perception* channel. → **frame the fields part as a cost result, not a new method.**

**New table competitors (the GT-free table-scoring goal is active):**
- **QUEST (2506.14568)** — GT-free table quality scoring via a **trained** quality-prediction model (training overhead + labels + a neural model at inference).
- **TSR-UQ (2407.01731)** — table-structure uncertainty via test-time augmentation + model agreement.

**Correction — our table scorer (was under-described as "independent OCR witness"):** Table-Trust is a **multi-signal structural scorer** — geometry/topology, structural plausibility, phantom/empty columns, span defects, cell-misalignment, concat-merge — **plus** content-conservation as *one optional* channel using an independent OCR witness, **and a without-witness mode** (HTML-structure signals only). Most signals are computed from the extracted output itself → **model-free**. This is a **distinct flavor** from QUEST (trained model) and Ajayi (self-confidence).

**Honesty on the cost claim:** state **"no extra LLM/VLM call,"** *not* literally "zero model call." The claim rests on **reuse**, not on "OCR isn't a model": the structural signals are genuinely model-free; the independent-OCR witness is **reused from the existing parse pipeline** (or, where a dataset ships no OCR, a single lightweight OCR pass). Note docTR and similar OCR *libraries* run neural models, so do **not** argue "OCR isn't a model" — argue "the OCR was already computed, and we never call an LLM/VLM." Airtight paper wording: *"Verification adds no extra LLM/VLM inference; structural signals are computed from the extraction output, and the optional OCR witness is reused from the pipeline (or a single lightweight OCR pass) — never a generative/vision-model call."*

**Go-condition is substantially met:** the hard question — *can a no-extra-LLM verifier match the expensive dual-model one?* — is **already answered YES internally** (the product's no-extra-LLM approach matched its two-LLM approach). Present as a **proprietary result**; replicate on public sets.

**Head-to-head / experiment plan (public):**

| Purpose | Dataset(s) | Note |
|---|---|---|
| **Primary P/L/V cost head-to-head** | **FATURA** | shared with P/L/V, rich, ROI-usable; **re-implement a P/L/V-style baseline** (cheap channels + dual-VLM validation) **and our no-call verifier on the SAME extractor outputs**; align metric (ROC-AUC, coverage @ ≤10% error) |
| Fields breadth (vs ExtractConf / ConfBench / Per-Field) | DocILE, CORD, **RealKIE-FCC** | RealKIE-FCC = ConfBench's set *and* our unstructured set → differentiate on *task* |
| Tables (vs Ajayi / QUEST / TSR-UQ) | ICDAR-2013 (+ RD-TableBench) | our multi-signal structural scorer vs self-confidence / trained scorer |
| Cost-win evidence | proprietary | no-extra-LLM matches dual-LLM |

**Final honest contribution framing:**
1. **Cost parity at no extra LLM/VLM call** — match dual-model verification's error-catching with no extra generative/vision call (proprietary + FATURA/DocILE/RealKIE-FCC). *Cost result, not a new fields method.*
2. **Cross-granularity** — one framework across fields + tables (tables = multi-signal structural scorer + optional cheap witness).
3. **Document detectability floor** — measure which document errors are uncatchable from in-document evidence, esp. the **systematic-confident-wrong** case P/L/V names but never measures. *The new-knowledge contribution.*

**Dataset status reminder:** VRDU = **FARA only** (our real ROI set); **Ad-buy = a comparison point, not our ROI set.** ROI = FATURA + FARA · Signal = RealKIE (+ DocILE) · Tables = RD-TableBench (+ DocILE LIR).

**Residual honesty guards:** fields method is a *cost result*, not novel; run the head-to-head **fairly** (same outputs, aligned metric); the **floor result must come out non-trivial** to carry the "new knowledge" claim; verify MSCE/IJDAR metadata before citing.
