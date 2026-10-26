# EBV Paper — Public Dataset Exploration (Fields)

**Purpose:** find 1–2 public datasets to benchmark the **field** verifiers (structured/ROI and unstructured/Signal) for the Evidence-Based Verification (EBV) paper. Tables already have a public benchmark (RD-TableBench); fields do not.
**Priority (as set):** mortgage documents first (so structured vs unstructured can be segregated); finance-related second.
**Date:** 2026-09-29 · **Last updated:** 2026-10-13 · **Status:** **FINALIZED v2** (see the "FINALIZED PLAN v2" section immediately below — it supersedes the 2026-09-29 picks). **Run-first:** FATURA-sample (structured) · RealKIE **FCC-Invoices** (unstructured) · RD-TableBench (tables, existing scores).

---

## ★ FINALIZED PLAN v2 (2026-10-13) — supersedes the 2026-09-29 picks below

This section records the dataset decisions after the full competitor-mapping + licensing + cost analysis (Oct 2026). The detailed exploration below (§0–§7) is the original backing; where it conflicts, **this section wins**. The driving principle shifted to: **prove our point against the *most-relevant competitor's* dataset, at the lowest extraction cost, with permissive licensing where possible.**

### A. Final decision

**Run-first set (cheap; what we extract + verify first):**
- **Structured (ROI) → FATURA, stratified sample** (~1–2k docs across all 50 templates × 24 fields, sized for ≥200 errors).
- **Unstructured (Signal) → RealKIE *FCC Invoices* subset** (370 docs; the single cheapest RealKIE subset *and* the one ConfBench uses).
- **Tables (Table-Trust) → RD-TableBench** (we already have predictions + Table-Trust scores → **zero new extraction cost**).

**Later, if cost/time allow (secondary):**
- **PubTabNet** (tables) — permissive + the RaV-IDP head-to-head + the academic standard reviewers expect.
- **FARA** (structured real-scan complement) — real scanned forms to complement synthetic FATURA.
- **CORD** (unstructured/receipts) — classic lineage + Gurram/ExtractConf-transfer comparison.
- **Other RealKIE subsets** (NDAs/Charities/SEC-S1) — domain variety (but costlier; S1/contracts are long).

**Dropped entirely:** **DocILE** — it was the *only* gated dataset (request form → token), and it is not needed: FATURA covers Jin, RealKIE covers ConfBench, CORD covers ExtractConf-transfer/Gurram. Removing it means **every remaining dataset is a direct download**.

### B. Dataset comparison table (verified Oct 2026)

| Dataset | Mode | Domain | Real/Synth | Docs | Pages/doc | Fields | GT | License | Source |
|---|---|---|---|---|---|---|---|---|---|
| **FATURA** | structured | invoices | synthetic | 10,000 (sample ~1–2k) | 1 | 24 (×50 templates) | bbox+text+class | **CC-BY-4.0** | Zenodo `records/10371464` (v2) |
| **FARA** (VRDU Reg.) | structured | US-gov registration forms | real-scan | ~1,915 | short | 6 (~15 usable cells, 3 templates) | human bbox+text, STL/MTL/UTL | **CC-BY** *(inferred; no LICENSE file)* | GitHub `google-research-datasets/vrdu` |
| **RealKIE — FCC Invoices** | unstructured | FCC political-ad invoices | real | 370 | ~5 (1–63) | 11 | OCR+text-span | **CC-BY-NC** | Zenodo `13327077` (`fcc_invoices.zip` 559 MB) |
| **CORD** | unstr./semi | restaurant receipts | real photo | 1,000 (800/100/100) | 1 | ~30 (5 super) | word-box+text+parse | **CC-BY-4.0** | HF `naver-clova-ix/cord-v2` |
| **RD-TableBench** | tables | complex real-world tables | real | 1,000 (461 EN used) | — | cells (HTML) | HTML (TEDS) | **CC-BY-NC-ND** | HF `reducto/rd-tablebench` |
| **PubTabNet** | tables | scientific/biomedical (PMC) | real (PDF-rendered) | ~568k (train ~500k/val ~9k/**test withheld**) | — | cells (HTML) | HTML structure+cell text+bbox (TEDS) | **CDLA-Permissive-1.0** | GitHub `ibm-aur-nlp/PubTabNet` |

**Other RealKIE subsets** (for later variety; same CC-BY-NC): NDAs 439 docs/~6 pg/**3 fields** (schema too thin); UK Charities 538/~16 pg/28 fields (long); SEC S1 **13,079 page-level items**/1 pg/24 fields (cheap per item, huge count); Resource Contracts 198/**~85 pg**/23 fields (very long, dearest).
**RealKIE extraction-cost ranking (cheapest→dearest, total pages):** FCC (~1,850) < NDAs (~2,634) < Charities (~8,608) < SEC-S1 (~13,079) < Resource Contracts (~16,830).

### C. Per-mode reasoning + closest competitor (head-to-head)

- **Structured → FATURA.** Closest competitor **Perception–Layout–Validation (Jin et al., 2026)** — a confidence-layer-over-extractions STP product (our near-twin) that gates with a **two-VLM** comparison (costly). Jin benchmarks on **FATURA** → direct head-to-head on our cost claim. FATURA also gives breadth (50 templates × 24 fields ≈ 1,200 field-location setups) that a general ROI claim needs.
- **Unstructured → RealKIE FCC.** Closest method **ExtractConf (Kumar, 2026)** (learned multi-signal confidence — our Signal-mode analog, but LLM-dependent: logprobs + 2 LLM passes → our cost contrast); closest *benchmark* **ConfBench (Roy, 2026)** (VLM trust-calibration + review-budget metric **on RealKIE-FCC**); rigor comparison **Gurram (2026)** (risk-controlled accept/route, CORD/FUNSD). FCC is genuinely variable-layout + cheapest + the ConfBench leg.
- **Tables → RD-TableBench (now) + PubTabNet (head-to-head).** Closest competitor **RaV-IDP (Jha, 2026)** — architectural twin (label-free table-fidelity scorer → routes low-fidelity to a **GPT-4.1 vision fallback**). **CONFIRMED real** (arXiv 2604.23644, primary-source verified) but a **single-author, non-peer-reviewed preprint** → cite+compare, but back it with peer-reviewed table-UQ (Ajayi, ICDAR-2013/GenTSR) + generic baselines (dual-parser, VLM-judge). RaV-IDP uses **PubTabNet** → PubTabNet is the head-to-head dataset. **No competitor uses RD-TableBench** → it gives no head-to-head (kept only as the "hardest real-world tables" stressor + because we already have scores).
- **Cost-claim bonus:** all three closest competitors spend an LLM/VLM at decision time (Jin's 2-VLM, ConfBench's VLM, RaV-IDP's GPT-4.1 fallback) → our "no extra LLM/VLM" has a clean target in every mode.

### D. Licensing (Infrrd legal **cleared** RealKIE + RD-TableBench on 2026-10-13)

- **Permissive — no legal needed, commercial-safe:** FATURA (CC-BY-4.0), CORD (CC-BY-4.0), PubTabNet (CDLA-Permissive-1.0), FARA (CC-BY *inferred* — confirm; no LICENSE file in repo, license only via Google's blog link).
- **Non-commercial — Infrrd legal CLEARED for research/benchmarking use (2026-10-13):** RealKIE (CC-BY-NC-4.0), RD-TableBench (CC-BY-NC-ND-4.0). Use = benchmarking + reporting scores only; **no redistribution of the data, no modified-copy republish (ND), no training the shipped product on them.**
- **Gated → dropped:** DocILE (research-access form → token; non-commercial; custom agreement). Not used.
- The **permissive backbone (FATURA, CORD, PubTabNet)** gives a head-to-head per mode even if NC were ever disallowed, so the paper is safe regardless.
- PubTabNet caveat: one HF mirror is mislabeled `cdla-sharing`; trust IBM's official LICENSE.md (= CDLA-Permissive-1.0). PubTabNet **test GT is withheld** → use train/val.

### E. Rejected datasets + why

- **DocILE for ROI** — 6,680 docs but 1,152 layout clusters (avg ~6/cluster, largest ~90) → few-shot-per-layout by design; can't do multi-template ROI. (Repurposed earlier for Signal/LIR, now dropped entirely — see §A.)
- **VRDU Ad-buy (DeepForm)** — the subset **Jin used** — rejected for *our* ROI: dozens of templates, **~20 docs/template, no per-doc template label, no STL split → can't group per template** to learn blueprints. (Jin can use it because its method calibrates **per field-type**, not per-template ROI.) So the Jin head-to-head runs on **FATURA**, not VRDU.
- **FARA as a *primary*** — only ~15 usable field×template ROI cells (3 templates × 6 fields; `foreign_principal` ~2.5%, `signer_title` 0.5–19% often unusable). Enough *docs* (~1,915) but too narrow in variety + no competitor overlap → **real-scan complement only**.
- **CORD as *primary* unstructured** — easy, semi-structured, single-domain receipts; high scores there are table-stakes (weak evidence) → **optional add only**.
- **PubTables-1M** (as 2nd table set) — CDLA-Permissive but GT is PASCAL-VOC **bbox/XML, not HTML** → needs a bbox→HTML conversion before TEDS. **FinTabNet/PubTabNet preferred** (full-table HTML). FinTabNet (CDLA-Permissive, HTML) is the other viable permissive table option if PubTabNet is unavailable.
- **RD-TableBench as the comparison axis** — no competitor uses it (and NC-ND) → kept only as the hardest-tables stressor + existing scores, not the head-to-head.
- (From §7 below, still rejected: ExtractBench, RealDocBench, DeepForm-for-ROI, BuDDIE/Kleister as primaries, FUNSD/SROIE/WildReceipt/EPHOIE/Form-NLU/KVP10k, Fannie/Freddie specs.)

### F. Sampling is accepted (and competitor-precedented)

Benchmarking on a **sample** (not the full set) is standard and reviewer-accepted, **provided** it is: stratified (cover all templates/fields, no cherry-picking), protocol reported, and large enough for stable numbers (≥200 errors + doc-level bootstrap CIs). **Jin benchmarked on a 200-doc sample of FATURA** (and 500 DocILE / 200 VRDU) — so our stratified ~1–2k FATURA sample is both normal practice and directly comparable to (indeed larger than) the competitor's setup.

### G. Access / download (all direct except the dropped DocILE)

- FATURA: `https://zenodo.org/records/10371464` (v2) — open, CC-BY-4.0.
- FARA (VRDU): `https://github.com/google-research-datasets/vrdu` — open; **real PDFs are bundled in-repo** (not annotations-only); archived but reachable.
- RealKIE: `https://zenodo.org/records/13327077` (or S3 `s3://project-fruitfly … --no-sign-request`; GitHub `IndicoDataSolutions/realkie`) — open download.
- CORD: HF `naver-clova-ix/cord-v2` (+ GitHub `clovaai/cord`) — open.
- PubTabNet: GitHub `ibm-aur-nlp/PubTabNet` (+ HF mirror) — open; test GT withheld.
- RD-TableBench: HF `reducto/rd-tablebench` — open (already local).
- ~~DocILE~~: form at `docile.rossum.ai` → token — **dropped**.

### H. Future considerations / open items

- **FATURA is synthetic → few natural errors.** Supply errors via the **corruption generator (spec E3a)** — mutate the gold (zero extraction cost). Natural errors primary where available; corruptions fill rare families.
- **Error target ≥200/testbed (field-instance level).** FCC: 370×11 ≈ 4,070 instances → ~400–800 errors ✓. FATURA sample sized to clear it. Whole-document-level counts on long-doc subsets would need combining — count at the field-instance level.
- **RealKIE train/val/test splits are not published** → we define our own **document-disjoint** splits (calibration ≠ test; freeze thresholds before test).
- **Confirm FARA's license** (no LICENSE file; CC-BY only via Google's blog) before relying on it.
- **Verify the remaining 2026 competitor citations** (Jin 2609.20110, ExtractConf 2606.24420, ConfBench 2608.01792, Gurram 2608.14639, DEC 2608.09842) the way RaV-IDP was primary-source-verified — before building comparisons on them.
- **Extractor choice** (what generates predictions on the public docs) is still open — an open-source VLM (self-hosted) avoids per-call fees for this volume; keep to short single-page docs to control token cost.

---

## 0. Frank headline

**There is no public, labeled, filled-mortgage key-information-extraction (KIE) dataset.** A targeted search returned only mortgage data *standards / schemas* — Fannie Mae/Freddie Mac's UMDP, URLA/ULAD (Form 1003), and the Uniform Closing Dataset (UCD). Those are MISMO XML *specifications*, **not** labeled document-image corpora with ground-truth fields. Everything else is vendor marketing.

**Why:** filled mortgage documents carry heavy PII (SSNs, income, addresses), so no labeled corpus is published. This is a hard constraint.

**Consequence:** mortgage results stay on **proprietary data**; the public leg for fields must be **finance-adjacent forms** (the agreed second priority). The structured/unstructured split still maps cleanly onto two public datasets (below).

---

## 1. Important clarification — none of these are "NTP" datasets

**Every public option is an *extraction* dataset, not a verification/NTP dataset.** This applies equally to *all* of them (FATURA, FARA/VRDU, RealKIE, DocILE, ExtractBench, RealDocBench). There is no public "NTP dataset" — nobody publishes extractions pre-labeled trustworthy / not-trustworthy; NTP is our framing.

Each public dataset gives `(document, ground-truth field values)`. To use *any* of them for EBV, we **build the verification layer ourselves**:

1. run an extractor → get predictions,
2. compare predictions to the dataset's GT → label each correct/wrong (this is `c`, per spec §8.1),
3. apply the verifier's evidence channels → measure error **detection**,
4. optionally inject corruptions (E3a) for more / rarer error types.

So the choice of dataset is about **which raw material best supports our channels and the two modes** — not about finding a ready-made NTP set.

---

## 2. Recommended datasets — per mode (finalized)

### 2.1 Structured / ROI mode → **FATURA** (primary, rich) + **FARA** (real complement)

ROI needs a **fixed template with many annotated docs per template** (≥~50 to learn a stable blueprint), across **multiple templates**, with **bounding boxes**. Only two public sets meet this — the richer-looking options (DocILE, VRDU Ad-buy) fail the docs-per-template test (verified below).

**FATURA — primary rich ROI leg**
- **10,000 synthetic invoice images · 50 templates · 24 field types · ~200 docs/template.** Invoice fields (total, date, invoice number, buyer info…) → finance-aligned. Bounding boxes + **intra-/inter-template splits** (intra = clean ROI; inter = unseen-template shift).
- **Why:** the only public set with *both* many templates *and* enough docs per template — far richer than FARA (50 templates × 24 fields vs 3 × 6).
- **Caveat (honest):** **synthetic** (generated from templates) — clean, no scan/OCR noise, so fewer *natural* extractor errors; lean on the corruption generator (E3a) for errors. Great for the ROI mechanism + detectability; it does **not** test real-scan robustness (FARA covers that).
- **Verify:** Zenodo license (likely permissive) and that annotations include bounding boxes.
- **Links:** arXiv:2311.11856 · Zenodo record 8261508.

**FARA (VRDU Registration Forms) — real-data complement**
- Real US-DOJ filings. **3 templates, 6 fields, ~1,915 docs (~400–640/template).** Public-domain gov docs (low license friction). Data = `dataset.jsonl` (OCR tokens + positions + GT entities with **bounding boxes**) + `meta.json` (type-specific match functions).
- **STL splits (per template):** Amendment (train ≤200 / test 300 / valid 100), Short-Form (≤200 / 300 / 100), Dissemination Report (≤200 / 150 / 50). **STL exists for FARA only.**
- **Per-template field coverage (exact, from split files):** all 3 templates nominally have all 6 fields, but density varies —
  - **Dissemination Report:** all 6 fields ~99% present → richest, 6 clean cells.
  - **Amendment:** 4 solid; `signer_title` 19%; `foreign_principal` 2.5% (unusable).
  - **Short-Form:** 5 solid; `signer_title` 0.5% (unusable).
  - → **~15 usable (field × template) ROI cells** total.
- **Why keep it:** real scanned docs → validates ROI under real-world noise, complementing FATURA's clean synthetic.
- **Links:** github.com/google-research-datasets/vrdu · arXiv:2211.15421.

**Rejected for ROI (verified — too few docs per template):**
- **VRDU Ad-buy (DeepForm):** 641 docs, dozens of templates, **no per-doc template label, no STL split** (VRDU skipped it), ~20 docs/template → can't group → not viable.
- **DocILE:** 6,680 docs but **1,152 layout clusters (avg ~6/cluster; largest only 90)** — few-shot-per-layout *by design*. Only a tiny head clears ~50. Not viable for multi-template ROI. *(Repurposed for Signal + tables — §2.2.)*

### 2.2 Unstructured / Signal mode → **RealKIE** (primary) + **DocILE** (optional)

**What Signal needs (grounded in the dociq code):** the signal functions take only **`(document text, field name, value)`** — `score_field_improved(text, field_name, value)`, where `text` = concatenated raw page OCR (`build_text_from_pages`). So a dataset needs just **document text + field name/value + GT + doc-type label** — **no bounding boxes, no images, no templates.** Variable layout is fine (Signal never groups by template). Much lighter bar than ROI.

**RealKIE (Indico) — primary Signal leg**
- 5 datasets; finance-relevant: **FCC Invoices, UK Charity Reports, SEC S1 Filings** (+ NDAs, Resource Contracts). Long, variable-layout docs with **OCR + text-span annotations** across 5 doc types.
- **Why:** meets every Signal requirement, finance-adjacent, realistic long/variable docs.
- **Download:** S3 `s3://project-fruitfly` · Zenodo record 13327077.

**DocILE — optional second Signal leg (repurposed)**
- The few-shot-per-layout that killed DocILE for ROI is **irrelevant for Signal** (no template grouping). It has text + **55 fields** + invoices (variable layout) → strong Signal fit, **and its LIR task = invoice line-item tables → also a public tables leg.**
- **Verify:** access/license (research-gated request form → likely non-commercial).
- **Links:** arXiv:2302.05658 · docile.rossum.ai.

**Backups (more doc-type variety):** BuDDIE (real US-gov business docs, 69 fields, 5 types — arXiv:2404.04003); Kleister-Charity (long finance annual reports — arXiv:2105.05796).

**Net:** structured/ROI = **FATURA (rich, synthetic) + FARA (real)**; unstructured/Signal = **RealKIE (finance, variable)**, optionally **DocILE** (which also yields a tables leg via LIR).

---

## 3. Mortgage-*inclusive* options (both NON-HELPFUL for this paper)

Two very recent (2026) benchmarks *contain* mortgage docs, but **neither is usable** for the EBV field study — for different reasons:

### 3.1 ExtractBench (LlamaIndex)
- **Size:** 370 docs / 4,869 pages / **67 document *types*** / 8 business domains. Includes **mortgage closing disclosures**.
- **The real limitation (refined):** 370 docs is *moderate*, not tiny — **but "67 types" means 67 *kinds* of enterprise documents (invoices, spec sheets, disclosures, …), not 67 mortgage subtypes.** Mortgage closing disclosure is **one type among 67** → ~5–6 docs/type on average → the *mortgage slice* is likely single-digit. Too small to build a benchmark on.
- **Templatic vs non-templatic split:** the dataset isn't designed with that axis, and per-type counts are too small to form two meaningful sub-benchmarks. **Cannot confirm a clean split without inspecting the data.**
- **Verdict: NON-HELPFUL** — the mortgage slice is too small to **train and test** on (~single-digit docs). Usable only for a qualitative peek at the mortgage subset, never as a benchmark.
- **Links:** paper arXiv:2607.29677 · HuggingFace `datasets/llamaindex/ExtractBench` (`uv run extract-bench download`)

### 3.2 RealDocBench
- **What:** 581 real docs, field-level QA over 4 domains (**mortgage + finance** among them), plus a layout track. *(We have already benchmarked Parse on this set.)*
- **The blocker:** it is **QA/layout-oriented and mixes document types without a templatic-vs-non-templatic axis**, so it **cannot be cleanly separated into structured (ROI) vs unstructured (Signal)** — which is exactly the split the paper's two modes require. Mortgage/finance relevance doesn't help without that separability.
- **Verdict: NON-HELPFUL** — it **cannot be split into structured (ROI) vs unstructured (Signal)** (no templatic axis), which is exactly what the two modes require. Mortgage/finance relevance doesn't help without that separability. Availability/licensing for outside use is also unclear.
- **Link:** arXiv:2606.07401 · (local eval docs already in the DocAI repo)

---

## 4. Caveats for using any of these

1. **They are extraction datasets, not NTP datasets** (see §1) — the verification layer is built on top by us.
2. **None is mortgage** — the public leg is for **reproducibility + generalization evidence** ("the method works on public finance forms too"), *not* to reproduce the proprietary mortgage numbers. Cross-domain results will differ; frame accordingly or a reviewer will ask why.
3. **Field schemas differ from mortgage** — confirm the field *types* (dates, currency, ids, names) exercise the same channel behaviours we rely on.

---

## 5. Recommendation summary

| Mode | Primary | Complement / optional | Notes |
|---|---|---|---|
| **Structured / ROI** | **FATURA** (50 templates × ~200 docs × 24 fields, synthetic invoices) | **FARA** (real gov forms, 3 templates × 6 fields, ~15 usable cells) | rich+synthetic paired with simple+real |
| **Unstructured / Signal** | **RealKIE** (FCC invoices, charity, S1) | **DocILE** (variable invoices, 55 fields; +tables via LIR) | Signal needs only text + field + GT (no boxes) |
| **Tables** | RD-TableBench (already have) | DocILE LIR (optional) | — |
| **Rejected for ROI** | — | VRDU Ad-buy, DocILE | too few docs/template (verified) |
| **Mortgage (public, labeled)** | — | ExtractBench / RealDocBench = non-helpful | doesn't exist (PII) / not splittable |

---

## 6. Open items / next steps

- [ ] **Verify licenses:** FATURA (Zenodo), FARA/VRDU, RealKIE, DocILE (research-gated → confirm commercial terms).
- [ ] **Confirm FATURA annotations include bounding boxes** (needed for ROI).
- [ ] **Confirm RealKIE field types** (S1 / charity / FCC) suit the field-verification setup.
- [ ] Decide whether to use **DocILE** as a second Signal leg and/or a public **tables** leg (via LIR).
- [ ] Decide whether to add a public **field** leg at all, or keep fields proprietary and rely on RD-TableBench (tables) as the sole public leg.

---

## 6a. References & links (for review)

**Recommended datasets**
- **FATURA** paper (arXiv:2311.11856): https://arxiv.org/abs/2311.11856 · data (Zenodo): https://zenodo.org/records/8261508
- **FARA / VRDU** dataset repo: https://github.com/google-research-datasets/vrdu · paper (arXiv:2211.15421): https://arxiv.org/abs/2211.15421
- VRDU code (google-research): https://github.com/google-research/google-research/tree/master/vrdu
- **RealKIE** paper (arXiv:2403.20101): https://arxiv.org/abs/2403.20101 · project: https://indicodatasolutions.github.io/RealKIE/ · Zenodo: https://zenodo.org/records/13327077
- **DocILE** (Signal + tables) paper (arXiv:2302.05658): https://arxiv.org/abs/2302.05658 · site + access form: https://docile.rossum.ai/
- **BuDDIE** (Signal backup, arXiv:2404.04003): https://arxiv.org/abs/2404.04003
- **Kleister** (Signal backup, arXiv:2105.05796): https://arxiv.org/abs/2105.05796

**Underlying source documents (browse the raw docs behind the datasets)**
- FARA — US DOJ National Security Division (Foreign Agents Registration Act): https://www.justice.gov/nsd-fara
- FARA e-File / registrant search (raw filings behind VRDU Registration Forms): https://efile.fara.gov/
- FCC Public Files (raw political-ad files behind DeepForm / VRDU Ad-buy): https://publicfiles.fcc.gov/
- DeepForm original project (FCC ad-buy extraction): https://github.com/project-deepform/deepform
- SEC EDGAR (source for RealKIE S1 filings & NDAs): https://www.sec.gov/edgar
- UK Charity Commission register (source for RealKIE charity reports): https://register-of-charities.charitycommission.gov.uk/

*(These are the canonical portals for those collections; verify exact links, as some pages may have moved.)*

**Mortgage-inclusive (both non-helpful — see §3)**
- ExtractBench paper (arXiv:2607.29677): https://arxiv.org/abs/2607.29677
- ExtractBench data (HuggingFace): https://huggingface.co/datasets/llamaindex/ExtractBench
- ExtractBench code: https://github.com/run-llama/ExtractBench
- RealDocBench (arXiv:2606.07401): https://arxiv.org/abs/2606.07401

**Mortgage data *standards* (specifications, not datasets)**
- Fannie Mae — Uniform Mortgage Data Program: https://singlefamily.fanniemae.com/delivering/uniform-mortgage-data-program
- Fannie Mae — URLA / Form 1003: https://singlefamily.fanniemae.com/delivering/uniform-mortgage-data-program/uniform-residential-loan-application
- Fannie Mae — URLA/ULAD FAQ: https://singlefamily.fanniemae.com/learning-center/delivering/faqs-uniform-residential-loan-application-uniform-loan-application-dataset
- Freddie Mac — Uniform Closing Dataset (UCD): https://sf.freddiemac.com/tools-learning/uniform-mortgage-data-program/ucd
- Freddie Mac — URLA/ULAD FAQ: https://sf.freddiemac.com/faqs/uniform-residential-loan-application-urla-uniform-loan-application-dataset-ulad-faq

---

## 7. Appendix — datasets considered but NOT adopted (for future reference)

Everything we evaluated and set aside, with the reason, so this isn't re-investigated later. (Adopted picks are in §2/§5.)

| Dataset | Considered for | Why not adopted | Could still be useful for |
|---|---|---|---|
| **VRDU Ad-buy (DeepForm)** | ROI | No per-doc template label; **no STL split** (VRDU skipped it); ~20 docs/template → can't group by template | UTL/shift only (optional) |
| **DocILE** *(for ROI)* | ROI | **Few-shot per layout by design** — 1,152 clusters, avg ~6 docs, largest only 90; only a tiny head clears ~50 | **Adopted instead for Signal + tables (LIR)** — see §2.2 |
| **ExtractBench** | mortgage field benchmark | 370 docs / **67 mixed doc types** → mortgage slice ~single-digit; not split into structured/unstructured | qualitative peek at the mortgage subset only |
| **RealDocBench** | mortgage/finance field benchmark | QA/layout-oriented; **cannot be split** into structured (ROI) vs unstructured (Signal) | already used to benchmark Parse separately |
| **BuDDIE** | ROI / Signal | 69 fields but ~6–7 docs per (state×type) template → too thin for ROI | Signal backup (variable-layout, rich schema) |
| **Kleister-Charity** | Signal | — (viable, just not primary) | Signal backup (long finance reports) |
| **FUNSD** | forms KIE | ~200 forms, generic Q/A/header entities, noisy — too small/generic | — |
| **CORD** | receipts KIE | ~1,000 receipts, variable layout, receipts ≠ our domain | possible Signal-ish, not chosen |
| **SROIE** | receipts KIE | ~1,000 receipts but only ~4 fields — too few fields | — |
| **WildReceipt** | ROI | ~1,765 receipts, 25 fields, but **designed for *unseen* templates** (variable) — not templatic | non-template / variable case |
| **EPHOIE** | ROI (templatic) | ~1,494 Chinese exam papers, 10 fields — templatic but **Chinese + niche domain** | — |
| **Form-NLU** | ROI/Signal | 857 form images, single-template multi-format — **too small** | — |
| **KVP10k (IBM)** | Signal | ~10k business docs, **generic key-value**, variable — not templatic, generic schema | possible Signal-ish, not chosen |
| **Payment dataset** | (contrast) | 14,237 invoices, **each from a different vendor → no shared templates** — opposite of ROI | the "no-template" extreme case, if ever needed |
| **Fannie/Freddie UMDP, URLA/ULAD, UCD** | mortgage | **Data *standards / MISMO XML specs*, not labeled document datasets** | schema reference only |

**One-line takeaway for future readers:** rich-schema + many-docs-per-template + public + real does **not** exist for the ROI paradigm — the rich sets (DocILE, Ad-buy) are few-shot-per-layout *by design*, and the many-docs-per-template set (FARA) is deliberately simple. FATURA (synthetic) is the only public set that gives both many templates *and* many docs per template. Mortgage-labeled public data does not exist (PII).

---

## Table-benchmark landscape — competitor benchmarks & rejection rationale (added 2026-10-23)

**Decision (FINALIZED): the tables leg uses RD-TableBench + ParseBench. Nothing else.**
Reasons: (1) both have the **GT format our scorer needs** (table **HTML** → TEDS-style /
witness-on-crop) and are in **our working domain** (business/financial/insurance tables,
where the model-free OCR witness works); (2) we **already have stored extractor outputs**
for both → **zero new extraction cost**; (3) every competitor benchmark is ruled out by at
least one hard blocker (scientific domain = witness-weak, structure-only = wrong task, too
small, wrong GT format, too large to re-extract, or **not released**).

### What each table-related competitor paper actually benchmarked on (read from the papers)
| Paper | Benchmark(s) used (from the paper) | Size used |
|---|---|---|
| RaV-IDP (2604.23644) | **PubTabNet val** (table fidelity); DocLayNet; DocVQA | PubTabNet **n=500** |
| Ajayi (2507.02009) | **ICDAR-2013** + **GenTSR** (scientific) | 20 + 39 = **59 tables** |
| TSR-UQ (2407.01731) | **ICDAR-2019 TSR** competition set | 543 imgs (100 test) |
| DEC (2608.09842) | **TableParseMap** (own) + Consensus-Hard Set; refs OmniDocBench v1.6 | TableParseMap **916** |
| QUEST (2506.14568) | **proprietary business** + **DocILE** | prop 1,000+10,000; DocILE 600+20,000 |

### Each public table benchmark (used by a related-work paper) — size, GT, license, why not usable
| Benchmark | Used by | Size | GT format | License (type) | Why not usable for our leg |
|---|---|---|---|---|---|
| **PubTabNet** | RaV-IDP | ~568k (val ~9k; **test GT withheld**) | HTML cells, TEDS | **CDLA-Permissive-1.0 — permissive (commercial-OK)** | Scientific/biomedical (PMC) = our OCR-witness's **weak domain** (OmniDoc-style over-rejection); test GT withheld |
| **ICDAR-2013** | Ajayi | ~150 (20 eval) | cell structure | no explicit license (research/competition use) | **TSR (table-structure-recognition) benchmark → wrong task**: scores structure recognition, not whether extracted *content* is faithful |
| **GenTSR** | Ajayi | 386 (39 used) | cell structure | no explicit license (research use) | **TSR → wrong task** (structure, not content); also tiny |
| **ICDAR-2019 cTDaR** | TSR-UQ | 543 (100 test) | TSR structure | no explicit license (research/competition use) | **TSR → wrong task** (structure recognition, not content verification) |
| **TableParseMap** | DEC | 916, failure-typed | HTML, TEDS | **not released yet** (no GitHub/HF as of 2026-10-23) | **Unavailable** — can't download. Best-*designed* for verification (failure-typed HTML GT); ~26% formula/symbol = witness-weak. **Future add if released.** |
| **OmniDocBench** | DEC (references); **we evaluated** | 1,651 pages (table subset) | HTML, TEDS | **research-only / non-commercial** (HF copyright statement) | Evaluated → **dropped** (`tables/paper/TABLES_EXPERIMENT.md` §4): AUROC(TEDS) 0.56 / vision 0.37; accepts only 1/38 good (97% false-alarm); witness fails on scientific/dense multi-column |
| **DocILE** | QUEST | **6,680 labeled** + 100k synth + ~1M unlabeled | **field bboxes, NOT table HTML** | gated token (docile.rossum.ai); **data license not stated** (code MIT) | **Wrong GT format** (field bboxes grouped into line items → no table-structure HTML to score) **and too large to re-extract** (running MinerU over a 6.7k+ set = heavy compute for a set that still has no table GT). Fields/Signal set, not tables |
| **proprietary (QUEST)** | QUEST | 1,000 + 10,000 | — | private | Not public |

### Our two chosen sets (for contrast)
| Benchmark | Size | Domain | GT | License | Role |
|---|---|---|---|---|---|
| **RD-TableBench** | 460 tables (461 EN) | real-world complex | HTML, TEDS | CC-BY-NC-ND (Infrrd legal cleared NC for benchmarking) | hard "catch" set; stored scores → zero re-extraction |
| **ParseBench** (our MinerU set) | 503 docs → ~314 single-table (we scored a random 60) | business/financial/insurance | HTML (`expected_markdown`) | internal/parse | realistic "coverage + zero-false-accept" set; stored outputs → zero re-extraction |

**One-line takeaway:** no *competitor* table benchmark is usable for us — **TSR/structure-recognition,
wrong task** (ICDAR-2013, ICDAR-2019, GenTSR); **scientific = witness-weak** (PubTabNet);
**wrong GT format + too large to re-extract** (DocILE: field-bboxes, 6.7k+ docs); **private**
(QUEST's own set); **not released** (TableParseMap — the one best-designed for verification).
OmniDocBench we evaluated directly and dropped (over-rejection). We proceed with
**RD-TableBench + ParseBench** (right GT format, our domain, stored outputs → zero
re-extraction). *(Not a competitor head-to-head on tables — the competitors differ
architecturally; see `..._related_work_v2.md` §9 and `tables/paper/TABLES_EXPERIMENT.md`.)*
