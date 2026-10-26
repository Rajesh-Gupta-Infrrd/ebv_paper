# EBV — Tables leg (Table-Trust scorer): public-benchmark evaluation

**Scope.** This is the tables leg of Evidence-Based Verification (EBV). It evaluates the
production **Table-Trust scorer** — a model-free verifier that assigns a continuous
`base_trust_score ∈ [0,100]` to an extracted table **with no extra LLM/VLM call** — on
**public table-extraction benchmarks**. The question for each benchmark is the same:
*without ground truth at run time, can the trust score separate a faithful extraction
(GOOD → accept) from a likely failure (BAD → route to re-extraction)?*

All numbers below are recomputed from stored results (no re-extraction). Language is kept
plain and genuine; we claim only what the stored results support.

---

## 0. TL;DR (what we will claim)

| Benchmark | Role | Headline | Verdict |
|---|---|---|---|
| **RD-TableBench** | hard set, "catch the garbage" | 78% defective; at trust≥85 **P 0.81 / R 0.86 / bad-catch 0.899** | ✅ in paper |
| **ParseBench** | realistic set, "high coverage, never wrongly accept" | **AUROC 0.912** (vision), catch **6/6**, **0 false-accepts**, coverage@5%-risk **0.88** | ✅ in paper |
| **OmniDocBench** | — | AUROC(TEDS) **0.561** / AUROC(vision) **0.368**; accepts only **1/38** good tables (97% false-alarm) | ❌ dropped |

**Two public benchmarks in the paper: RD-TableBench + ParseBench.** They are
complementary — RD proves the scorer *catches* bad extractions on the hardest set;
ParseBench proves it gives *high coverage with zero false-accepts* on realistic
insurance/financial tables. OmniDocBench is not a usable verification benchmark for this
scorer (reasons in §4).

---

## 1. Shared method (all benchmarks)

- **Scorer.** `scripts/extract/table_extractor/scoring.py :: score_table_trust(...)`.
  Model-free: structural HTML signals (geometry/topology, structural plausibility) +
  a **content-conservation witness** (independent docTR OCR over the table region) →
  `base_trust_score`, `reason_codes`, `critical`, `failure_family_hint`. **No LLM/VLM in
  the scorer** (the VLM lives only in the separate refiner stage, which we do not use for
  scoring).
- **No re-extraction.** We reuse the already-finalized extractor outputs (MinerU for
  ParseBench/RD; the stored refiner run for OmniDoc) and run only the scorer. For the
  witness, docTR runs on the **table region cropped from the page image** via the
  extractor's reported `bbox.normalized` (bbox-clipped witness — the fix for the earlier
  full-page-witness bug).
- **Decision rule.** Production threshold: **ACCEPT iff `base_trust_score ≥ 85`**, else
  route to re-extraction. False-accept (bad table passed downstream) is expensive;
  false-reject (good table re-extracted) is cheap → the scorer is precision-first, its
  core job is bad-catch.
- **Labels (GOOD/BAD).** A table is GOOD if its extraction is faithful to the table in
  the page image, else BAD. How this label is obtained is **the central methodological
  issue** and differs by benchmark — see §3 (ParseBench) for why tree/string metrics
  (TEDS) are **not** valid faithfulness labels, and why we adjudicate visually.

---

## 2. RD-TableBench (finalized — see pushed doc)

Full write-up: `DocAI/docs/Table_Trust_Scoring_RD_TableBench_Evaluation.md` (committed).
Summary only here, for context:

- **Set.** 460 tables, **361 (78%) BAD** — a very hard, defect-heavy set. GT labels are
  human-adjudicated (RD's own GT is often wrong, so adjudication was necessary; this is
  internal and not claimed in the paper).
- **Result** (identical rocket-domain config, no re-tuning; trust≥85): **Precision 0.81,
  Recall 0.86, bad-catch 0.899** (rejects ~90% of genuinely-bad tables). This is a pure
  *generalization* test of a scorer built on a different domain, evaluated as a
  precision-first **catch classifier**.
- **Role in paper.** The "catch the garbage" benchmark: on the hardest public set the
  scorer still routes the large majority of bad extractions to re-extraction. (We do
  **not** claim coverage on RD — at 78% defective there is little to auto-accept.)
- Internal-only mechanics (witness bbox-clipping, either-or scoring of header/caption
  drops, formula-table handling) stay in the pushed doc and are **not** surfaced in the
  paper.

---

## 3. ParseBench (new, fully computed here) — ✅ in paper

### 3.1 Setup
- Source: finalized **MinerU** outputs, `eval/table_extraction/parsebench/outputs/mineru_v3/*.json`
  (503 documents). We select pages with exactly **one** `<table>` block carrying a bbox
  and a matching page image (~314 such single-table pages).
- We scored a **random sample (seed 42) of 60** single-table pages; **59 returned a trust
  score** (1 page, idx31, returned no trust and is excluded). Each scored page has: the
  predicted table HTML, the trust score + reason codes, the **table crop** (page image ×
  bbox), the ParseBench GT (`expected_markdown`, which is HTML), and a computed TEDS.
- docTR witness ran on the bbox-clipped crop (`run_doctr_if_needed=True`).

### 3.2 Why TEDS≥0.9 is NOT a valid label here
We first tried the standard label **GOOD = TEDS ≥ 0.9**. It gives **AUROC(trust, TEDS≥0.9)
= 0.543** — near chance. But that is a **label failure, not a scorer failure**:

TEDS is a tree-edit distance over the predicted **HTML tree vs the GT HTML tree**. It
penalizes *rendering* differences that do not change the information:
- `<th>`/`<thead>` tags vs `<td>` — e.g. **idx42** (Rule Name / Basic Limit): extraction
  is faithful to the image, GT uses `<thead>`/`<th>` → **TEDS 0.50**, scorer correctly
  accepted (trust 100).
- different column grouping of identical content — e.g. **idx40** (CA Territory Factors):
  the page and the extraction are an 8-column two-up layout; GT stores the same zip codes
  as a 4-column single list → **TEDS 0.54**, scorer correctly accepted (trust 100).
- phantom/empty columns that mirror real visual gutters, extra empty rows, multi-line
  cell handling.

So TEDS measures *"does my HTML tree equal the GT tree,"* not *"did I capture the
content."* Only **24/59** tables pass TEDS≥0.9, yet by visual check **53/59** are
faithful. TEDS is the wrong instrument.

### 3.3 We searched for an objective GT-based label — none reproduces faithfulness
We swept GT-based labels (pred-vs-GT) and measured agreement with the visual label and the
resulting AUROC(trust):

| Label | #called-BAD | agreement w/ vision | real failures caught (of 6) | AUROC(trust) |
|---|---|---|---|---|
| TEDS≥0.9 | 35 | 0.51 | 6/6 | 0.543 |
| TEDS≥0.5 | 6 | 0.90 | 3/6 | 0.706 |
| **content-F1≥0.9** (best) | 7 | **0.92** | 4/6 | **0.732** |
| content-recall≥0.8 | 7 | 0.92 | 4/6 | 0.732 |
| numeric-recall≥0.8 | 7 | 0.92 | 4/6 | 0.713 |
| **visual adjudication** | 6 | — (reference) | 6/6 | **0.912** |

(content-F1 = multiset token-overlap F1 between predicted cell text and GT cell text,
structure ignored.)

**The best automatic label (content-F1≥0.9) still fails in both directions**, for
fundamental reasons, which is why its AUROC is only 0.73:
- **Misses real failures** (token overlap is blind to layout): **idx35** (discount matrix,
  values in wrong columns) content-F1 **0.99**; **idx51** (actuarial table, a whole
  sub-block dropped) content-F1 **0.99** — both caught by the scorer (trust 34, 60).
- **Falsely flags faithful tables** because the GT is a *different rendering*: **idx26**
  content-F1 **0.42** (TEDS −0.04) and **idx43** **0.71**, both faithful to the image and
  correctly accepted by the scorer (trust 100, 86).

Root cause (shared by TEDS and content-F1): they compare predicted HTML to GT HTML, but
ParseBench GT is a differently-rendered tree, so string/tree comparison conflates
*rendering* with *extraction error*. The scorer avoids this entirely — its witness reads
the **crop (image)**, not the GT HTML.

### 3.4 Primary label = visual adjudication (and how we keep it objective)
We label each of the 59 tables by **visually adjudicating the predicted table against its
crop** (every crop was read against its predicted HTML this session). Result: **53 GOOD /
6 BAD (10% BAD)**.

- **AUROC(trust, vision) = 0.912**
- **Bad-catch = 6/6 = 100%** — every genuinely-bad extraction got trust < 85.
- **False-accepts (FP) = 0** — the scorer never accepted a bad table.
- **False-alarm = 16/53 = 30%** — it also rejects faithful tables (the cost of being
  conservative; almost all are MinerU multi-line-cell *concatenations* that the scorer
  penalizes though the content is present).
- **Coverage@5%-risk = 0.88** (auto-accept 88% of tables under a 5% error budget);
  @10% = 0.97; @20% = 1.00.
- accept@85 confusion vs vision: TP=37, FP=0, TN=6, FN=16.

The 6 BAD tables and their trust (all < 85, i.e. all caught):
idx35 (33.9), idx29 (43.7), idx12 (53.7), idx51 (59.8), idx24 (71.7), idx23 (80.2).

**Keeping vision objective (not "we eyeballed it"):** the visual labels agree with the
objective **content-F1≥0.9** label on **92% (54/59)** of tables — so the labels are
reproducible, not hand-picked. We report TEDS≥0.9 = 0.543 **in the paper** as the
*motivation* for visual adjudication (turning a metric limitation into a finding:
tree/string table metrics are not valid verification labels), and optionally report
content-F1≥0.9 → AUROC 0.73 as an honest conservative floor (the gap to 0.912 is label
noise — the automatic label can't see misalignment/partial-drops).

### 3.5 Concrete discrimination example (good for the paper)
Same document type, opposite outcomes — the scorer tells them apart:
- **idx29** "Weekdays → Manhattan" subway schedule: extraction **mangled** (bogus
  `rowspan=10`, mostly empty), TEDS 0.02 → scorer trust **3.8** (rejected).
- **idx46** "Weekdays → The Bronx" subway schedule (same source style): extracted
  **cleanly** → scorer trust **99** (accepted).

### 3.6 Honest caveats
- It is an **easy set**: only 6/59 (10%) are truly bad, because MinerU extracts most
  ParseBench tables faithfully. The AUROC rests on a small bad-sample (n=6); the robust,
  CI-free facts are the **100% catch** and **zero false-accepts**.
- The scorer trades a **30% false-alarm** for perfect catching (conservative operating
  point) — state this plainly.

---

## 4. OmniDocBench (new, fully computed here) — ❌ dropped

### 4.1 Setup
- The table refiner was run on OmniDocBench (stored, recent):
  `eval/parse/omnidoc-bench/outputs/auto_table_refined/auto/cases/*/document_surface.json`
  carry `table_refinement.trust_score_before` for the extracted table blocks (308 blocks
  with a trust value). GT tables in `OmniDocBench/OmniDocBench.json`; each case has an
  `input.png`.
- **TEDS track:** 107 single-table pages pairable to the GT → TEDS computed per page.
- **Vision track:** 40 single-table crops (those with an available page image and non-empty
  HTML) were visually labeled → **38 GOOD / 2 BAD** (idx7, idx29).

### 4.2 Results — both labels say it does not work
- **AUROC(trust, TEDS≥0.9) = 0.561** over 107 pages. Note **78/107 (73%)** pass TEDS≥0.9 —
  a good-heavy set, so there is very little bad signal to separate.
- **AUROC(trust, vision) = 0.368** over the 40 labeled crops — **below chance**.
- **The scorer over-rejects:** of 38 vision-GOOD tables it accepts only **1** at trust≥85
  → **false-alarm ≈ 97%**. (Both vision-BAD tables, trust 56.7 and 77.1, are correctly
  rejected, but n=2 is too small to carry a benchmark.)
- Trust on labeled crops: min 12.2, median 63.0, max 99.5 — depressed across the board,
  including on faithful tables.

### 4.3 Why it fails (two independent reasons)
1. **The scorer's witness fails on OmniDoc content.** OmniDoc tables are dominated by
   scientific / dense multi-column / regression-style tables. The independent docTR
   witness cannot reliably re-read these (sub/superscripts, stars, tight multi-column
   numerics), so content-conservation looks low even when the extraction is faithful →
   the scorer rejects good tables (97% false-alarm). This is a witness/OCR limitation on
   this content domain, not a sign the extractions are bad — vision confirms they are
   nearly all faithful.
2. **The set carries almost no verification signal.** Like ParseBench the extractor is
   mostly faithful (38/40 GOOD), but *unlike* ParseBench the scorer does not separate the
   few failures — vision AUROC is below chance. There is nothing to claim.

### 4.4 Decision
OmniDocBench is **not a usable verification benchmark for this scorer** and is **dropped**.
We keep the negative result documented (TEDS 0.561, vision 0.368, 97% false-alarm) because
it cleanly delimits where the model-free witness works (financial/insurance/business
tables — ParseBench, RD) and where it does not (scientific/dense multi-column — OmniDoc).

---

## 5. Cross-benchmark synthesis (framing for the paper)

- **The label matters more than the metric.** TEDS (and content-overlap) compare predicted
  HTML to GT HTML; they conflate *rendering* with *faithfulness* and are therefore invalid
  verification labels (ParseBench: TEDS≥0.9 → AUROC 0.54 vs vision 0.91; OmniDoc:
  TEDS 0.56). The honest signal comes from adjudicating the predicted table against the
  **image**.
- **Two complementary public benchmarks:** RD-TableBench (hard, 78% bad → *catch*:
  bad-catch 0.899) and ParseBench (realistic, 10% bad → *coverage with zero false-accept*:
  AUROC 0.912, cov@5% 0.88). Together they show the scorer both rejects garbage and
  safely auto-accepts the large majority of faithful tables, **with no extra model call**.
- **Scope boundary (stated honestly):** the model-free witness works on
  financial/insurance/business tables; it does not work on scientific/dense multi-column
  tables (OmniDoc), where it over-rejects. This is a limitation, not hidden.

---

## 5b. Why only these two public sets — competitor-benchmark landscape (2026-10-23)

We checked the table benchmarks used by the related-work table papers (read from the
papers, not our notes) and ruled each out for our scorer. Our scorer needs an extracted
table **HTML** + the table **image** + a table GT (HTML/TEDS-style), and works on
business/financial tables (it over-rejects scientific/dense — see §4).

**What each competitor paper benchmarked on (from the papers):**
| Paper | Benchmark(s) used | Size used |
|---|---|---|
| RaV-IDP (2604.23644) | **PubTabNet val**; DocLayNet; DocVQA | PubTabNet n=500 |
| Ajayi (2507.02009) | **ICDAR-2013** + **GenTSR** (scientific) | 20 + 39 = 59 |
| TSR-UQ (2407.01731) | **ICDAR-2019 TSR** | 543 imgs (100 test) |
| DEC (2608.09842) | **TableParseMap** (own) + Consensus-Hard; refs OmniDocBench | 916 |
| QUEST (2506.14568) | proprietary business + **DocILE** | prop 1k+10k; DocILE 600+20k |

**Each public table benchmark (used by a related-work paper) — size, GT, license, why not usable:**
| Benchmark | Used by | Size | GT format | License (type) | Why not usable for our leg |
|---|---|---|---|---|---|
| **PubTabNet** | RaV-IDP | ~568k (val ~9k; test GT withheld) | HTML, TEDS | **CDLA-Permissive-1.0 — permissive (commercial-OK)** | Scientific/biomedical = witness-weak (OmniDoc-style over-reject); test GT withheld |
| **ICDAR-2013** | Ajayi | ~150 (20 eval) | cell structure | no explicit license (research/competition) | **TSR (structure-recognition) → wrong task**: scores structure, not extracted-content faithfulness |
| **GenTSR** | Ajayi | 386 (39 used) | cell structure | no explicit license (research) | **TSR → wrong task** (structure, not content); also tiny |
| **ICDAR-2019 cTDaR** | TSR-UQ | 543 (100 test) | TSR structure | no explicit license (research/competition) | **TSR → wrong task** (structure recognition, not content verification) |
| **TableParseMap** | DEC | 916, failure-typed | HTML, TEDS | **not released** (no GitHub/HF, 2026-10-23) | Unavailable — can't download; best-designed for verification; ~26% formula/symbol = witness-weak. Future add if released. |
| **OmniDocBench** | DEC (ref); **we evaluated** | 1,651 pages | HTML, TEDS | **research-only / non-commercial** | Evaluated → dropped (§4): AUROC(TEDS) 0.56 / vision 0.37; 97% false-alarm |
| **DocILE** | QUEST | 6,680 labeled + 100k synth + ~1M unlabeled | **field bboxes, NOT table HTML** | gated token; **data license not stated** (code MIT) | **Wrong GT format** (field bboxes → no table HTML) **and too large to re-extract** — running MinerU over a 6.7k+ set is heavy compute for a set that still has no table GT. Fields/Signal set, not tables. |
| proprietary (QUEST) | QUEST | 1k+10k | — | private | Not public |

**Conclusion:** no competitor table benchmark is usable for us — TSR/structure-recognition
(wrong task: ICDAR-2013/2019, GenTSR), scientific (witness-weak: PubTabNet), wrong GT format
+ too large to re-extract (DocILE), private (QUEST's own set), or unreleased (TableParseMap);
OmniDocBench we evaluated and dropped. We proceed with **RD-TableBench +
ParseBench**: the right GT format (HTML/TEDS), our working domain, and **stored extractor
outputs → zero re-extraction cost.** This is also why the tables leg is an *architectural*
comparison (no extra model call, model-free witness), not a same-benchmark head-to-head —
the competitors differ in mechanism and evaluate on sets we cannot or should not use. Full
landscape also in `evidence_based_document_ai_verification_dataset_exploration.md`.

---

## 6. Standing rules & traceability

- Simple, genuine language; **claim only from stored results**; publish NUMBERS not DATA;
  no rerunning encouraged.
- Production repo `dociq` untouched; all scoring used the DocAI `eval/` code + stored
  outputs. No extra LLM/VLM call in any scorer run.
- **Stored artifacts (this leg).** Persisted under `tables/analysis/` next to this doc:
  - ParseBench: `pb_manifest.json` (60 records: idx, crop path, pred HTML, trust,
    reason_codes, accept@85, gt_md, teds), `pb_crops/` (60 crops), `pb_vision_auroc.py`
    (AUROC/coverage/confusion), `pb_labelsweep.py` (GT-label sweep), `pb_score.py`
    (scorer runner), `pb_html_dump.txt`.
  - OmniDoc: `omnidoc_teds.json` (107 pages: trust_before, teds), `omnidoc_vlm_manifest.json`
    (40 crops), `vlm_labels.json` (40 vision labels), `omnidoc_crops/` (40 crops),
    `omnidoc_teds.py`, `omnidoc_crops.py`.
  - Vision labels for ParseBench are embedded in `pb_vision_auroc.py` (the `vision` dict).
- RD-TableBench canonical write-up: `DocAI/docs/Table_Trust_Scoring_RD_TableBench_Evaluation.md`.
