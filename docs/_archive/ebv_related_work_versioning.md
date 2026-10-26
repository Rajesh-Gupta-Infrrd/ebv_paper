# Related Work — Version History & Decisions (traceability)

Tracks how the Related Work section evolved. The *finalized* prose lives in `ebv_paper.md`; this file keeps every version + the reasoning, so nothing is lost.

---

## Lineage of this section (pre-prose planning)

- **v0 — raw must-cite list** (`…_related_work.md` §2): first grouped list of foundational papers (selective prediction, conformal, LLM uncertainty, fact verification, reference-free QE, ensemble diversity, doc-KIE, doc/table eval).
- **v1 — coverage + first threats** (`…_related_work.md` §3): added the crowded 2026 neighbourhood; flagged that the "detectability frontier" concept = Rabanser's selective-classification gap.
- **v2 — post full-text debate** (`…_related_work_v2.md`): two agents read the closest papers in full, moderated. Locked the honest framing and the §A–D presentation order; re-anchored the floor lineage; corrected the table-scorer description; fixed the cost wording.

## Draft v1 (prose) — current, in `ebv_paper.md`

Five grouped paragraphs + a positioning paragraph, in the fixed order:
§A confidence/selective-acceptance for KIE (HYCEDIS → ExtractConf → ConfBench → Per-Field Risk Control → Perception–Layout–Validation) · §B tables & cross-granularity (Ajayi 2025/2024, QUEST, diagnosis-correction, RaV-IDP) · §C selective prediction + the floor (Chow; El-Yaniv/Wiener; Geifman/El-Yaniv; conformal; Rabanser & Papernot; Pandey et al.) · §D reference-free QE + LLM uncertainty (Rei; semantic entropy; SelfCheckGPT; P(True)) · Positioning.

---

## Draft v2 (current, in `ebv_paper.md`) — refinements from review

1. **"The closest system to ours" → "Most closely related to our work is…"** (more conventional/formal).
2. **DEC now described by its detection *mechanism*** (confirmed full read: Xiao et al., 2026 — a VLM "visual-consistency" controller comparing the parse to the source image; extra VLM calls; no floor) — related work should say *how* prior work detects.
3. **Split the selective-prediction sentence** so the deep-net *treatment* (Geifman & El-Yaniv) and the *metric* (risk–coverage / AURC) are separate, not conflated.
4. **Rabanser & Papernot marked "in general classification settings"** so it's clear it's not on documents (our specialization is the new step).
5. **Reference-free QE reframed as an analogy** (applies to document extraction), not implying we do MT.
6. **Removed the "not ground-truth-free" claim** from Related Work (→ Intro/Method/Limitations).
7. **Each body block ends with a neutral "However, …" gap sentence** (ACL convention); no "ours is best" claims in the body.
8. **Own contribution moved to an unlabeled closing paragraph**; **removed the "Positioning." heading** (labelled "Positioning" reads unprofessional).

Carried-forward notes: ConfBench and the QE paragraph are the most *droppable* if space is tight; Per-Field Risk Control's "guarantees" are cited *neutrally*, not set up as a bar we must meet (we don't claim formal certification — connects to the optional sufficiency idea).

## Draft v2.1 (user polish, 2026-10-07) — supersedes two v2 items

- **§A:** kept the hybrid "three limitations" ending; removed stray quotation marks + double space.
- **§B (DEC):** reverted to the lighter *"detects and repairs … with an agentic vision-model controller"* — related work need not give the in-depth detection mechanism (**supersedes v2 item 2**). Also fixed wording: "signal *using* a VLM fallback" → "signal, *with* a vision-language-model fallback."
- **§D:** **removed** the "However" drawback sentence — the gap-ending convention applies to *direct-competitor* blocks (tables), **not** to analogue/ancestor groups like QE/uncertainty (**refines v2 item 7**: "However" is not on every block).
- **Closing:** "so as to measure" → "to measure"; the long sentence split into three for readability.

---

## Decisions & reasoning (why it reads this way)

1. **Order = direct competitors first, theory last, positioning at the end.** §A opens on the nearest work (document-KIE confidence) so the reader feels the crowded space immediately and we can land one shared verdict (fields-only / extra model call / no floor). Theory (§C/D) comes later as the frame we *specialize*, so the positioning paragraph reads as the natural next step. *(This is the §A–D plan from the v2 doc.)*
2. **Honest framing, not "three firsts."** The positioning paragraph claims an **integration + a measurement**, explicitly *not* a new confidence concept. Reason: the full-text debate showed each pillar is anticipated; overclaiming invites a desk reject.
3. **Rabanser & Papernot (2025) cited as the concept we *specialize*, not invent.** Reason: our "detectability frontier" is their selective-classification gap / Bayes-noise floor, applied to document evidence. Pretending otherwise is the single biggest novelty risk.
4. **"detectability," not "floor," in the prose.** We *measure* catchable vs. not (a map + an honest residual) and scope the genuinely-uncatchable cases to adjudicated source-ambiguous errors — we do **not** assert proven impossibility.
5. **Cost claim stated precisely as "no additional LLM/VLM call."** The independent-OCR witness is described as *reused from the parse pipeline*; we avoid "zero model call" and never argue "OCR isn't a model" (docTR runs neural models — the claim rests on *reuse*).
6. **Fields framed as a cost result, tables as the more distinct contribution.** Perception–Layout–Validation is named as the near-twin on fields; our fields novelty is the *no-LLM/VLM instantiation*, not the signals→fuse→route idea. The independent-witness table scorer is positioned as complementing (not beating on concept) the self-confidence / VLM table methods.
7. **Not GT-free.** Explicitly stated against the QE comparison, because our ROI blueprints / classifiers are learned offline.
8. **The systematic-confident-wrong case is the hook into our contribution.** Jin et al. (2026) *name* it but do not analyze it; we use that as the concrete, citable gap our floor study fills.

## Citation keys to VERIFY before submission (⚠️)
- **Confident**: Rabanser & Papernot 2025 (2510.20242); Perception–Layout–Validation = Jin et al. 2026 (2609.20110); ExtractConf = Kumar 2026 (2606.24420); ConfBench = Roy et al. 2026 (2608.01792); Per-Field Risk Control = Gurram 2026 (2608.14639); RaV-IDP = Jha 2026 (2604.23644); Pandey et al. 2026 (2608.23663); HYCEDIS = Nguyen et al. 2021 (2206.02628); Ajayi et al. 2025 (2507.02009).
- **Verify authors/keys**: the table-UQ paper (2407.01731), the diagnosis-correction table paper (2608.09842), and exact years/venues for the foundational anchors (Chow 1970; El-Yaniv & Wiener 2010; Geifman & El-Yaniv 2017/2019; Angelopoulos et al.; Rei et al. 2020/2022; Kuhn et al. 2023 / Farquhar et al. 2024; Manakul et al. 2023; Kadavath et al. 2022).
- ✅ **QUEST VERIFIED (2026-10-09):** arXiv 2506.14568 = "QUEST: Quality-aware Semi-supervised Table Extraction for Business Documents," **Thomas, Coustaty, Joseph, Deloin, Carel, Poulain D'Andecy, Ogier — cite as (Thomas et al., 2025), ICDAR 2025.** Model = **XGBoost regressor over hand-crafted structural/contextual features + extractor confidences** (NOT vision/VLM/LLM). **Does NOT check content fidelity against the page** (predicts an F1 score from features) → our independent-OCR-witness is a real differentiator. Reference-free **at inference only** (needs GT F1 at training). **Tables-only.** **No detectability analysis.** Paper updated: "(Anonymous, 2025)" → "(Thomas et al., 2025)" and "without ground truth" → "without ground truth at inference" (user chose fixes 1+2; declined the optional fidelity-contrast sharpening #3 — the fidelity differentiator stays in the closing paragraph via our method).
- SIEVES (2604.25855) and the AURC metric paper are cited conceptually; decide whether to include explicitly.

## Claim-integrity pass (2026-10-09) — "model call" → "LLM or VLM call"

Triggered by the user noticing the title's "Without Extra Model Calls" was an overclaim (we *do* use models: tabular classifiers in the signal mode, docTR OCR as the table witness / reused pipeline OCR). The precise, airtight claim is **no additional LLM or VLM call** (docTR is OCR, not LLM/VLM, and reused; classifiers are small, local, non-generative).

Applied:
1. **Title** (`ebv_paper.md` line 1): "…Without Extra **Model Calls**" → "…Without Extra **Language- or Vision-Model Calls**" (option B). Body was already precise ("no LLM or VLM inference"); only the title was loose.
2. **Related Work Para A**: "they spend at least one additional **model call** at decision time" → "…additional **LLM or VLM call**…" (the cited examples — ExtractConf's two LLM passes, P/L/V's two-VLM comparison — are already LLM/VLM).

Full consistency check (confirmed OK, no other change needed):
- Every drawback we attribute to a model/LLM/VLM call = LLM or VLM: ExtractConf (LLM), P/L/V (VLM), DEC (vision-model), RaV (VLM fallback).
- Non-LLM/VLM methods are NOT faulted for a model call: HYCEDIS (conformal — faulted for stack-tie + GT training), Per-Field Risk Control (conformal, neutral), **Ajayi** (own pipeline confidence — distinguished on *independence/fidelity*, not cost), **QUEST** (trains a dedicated quality model — distinguished on the *detectability gap*, not cost). We use models too, so we only ever claim "no extra **LLM/VLM**," never "no model."
- Closing paragraph already precise + hedged: "**almost always** with at least one additional **LLM or VLM** call" (hedge covers Ajayi/QUEST); contribution framed as "integration + detectability study," never "first no-model method."

Open / to decide later (user: "then we will decide the changes"):
- Optional: sharpen the independent-witness / content-fidelity contrast vs Ajayi + QUEST (our witness verifies fidelity against an independent reading; learned-quality / own-confidence methods don't). **Blocked on verifying QUEST's actual architecture** (unverified "Anonymous" citation — don't claim vision-vs-ML until checked).
- Also update the title in the spec doc (`evidence_based_document_ai_verification_research_spec_v3.md` title-locked block) to match, before submission.

## Ajayi content-fidelity tweak + Intro to-do (2026-10-09)

- **Ajayi sentence (Para B)**: "…rather than **cross-checking the extraction against an independent reading**;" → "…rather than **verifying content fidelity against an independent reading of the page**;" (user approved option a). *Why:* names *what* the independent reading provides (a content-match check against the page) — which own-confidence aggregation can't do — setting up our independent-witness contribution. Chose this over the dangling "…for content fidelity."
- **TO-DO (Introduction):** add the motivation that **content-fidelity verification matters especially for modern VLM/LLM extractors (which can hallucinate content not on the page)** — held OUT of the Ajayi sentence because (i) it's editorial for a describe-others sentence and belongs in the Intro's motivation, and (ii) Ajayi is table-structure-recognition UQ, not a VLM method, so attaching it there would conflate.

## HYCEDIS boomerang fix (2026-10-13)
- Removed "**and require ground-truth training**" from the HYCEDIS description (§A). *Why (user caught):* HYCEDIS fuses signals + trains a model on GT — which is exactly what WE do (Signal classifiers + ROI blueprints are GT-trained). Faulting HYCEDIS for GT-training boomerangs on us (we're not GT-free). Kept only "tied to a specific extraction stack" (a genuine distinction — see note). HYCEDIS public benchmarks: SROIE (main) + CORD (OOD); + in-house Japanese invoices.
- **OPEN:** "tied to a specific extraction stack" is our *characterization* (HYCEDIS consumes a pipeline's intermediate OCR / box-localization / key-value-recognition signals, so it needs a stack that exposes them) — NOT a limitation HYCEDIS itself states. Defensible distinction from us (we score from the extraction output + document + reused OCR, not the extractor's internal module confidences), but consider rewording to "relies on a pipeline's intermediate signals" for precision. Pending user call.

## Open items / possible refinements (for discussion)
- Decide whether to add a dedicated sentence on **our own prior Table-Trust system** (self-citation, anonymized for review) or fold it into Method only.
- Decide whether §D's QE + uncertainty paragraph should be shortened if space is tight (it's the least-central group).
- If venue = main track, consider expanding the P/L/V contrast into 2–3 sentences (it's the sharpest "why not just them" question).
