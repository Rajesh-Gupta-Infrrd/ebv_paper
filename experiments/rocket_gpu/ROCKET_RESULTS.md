# ROCKET — unified-system verification on a proprietary mortgage dataset

Purpose: demonstrate the **one unified verifier across all three modes on the same real
document pool** (Infrrd ROCKET mortgage / loan-origination files). Extractor = NuExtract-3
(fields, via vLLM) and MinerU (tables), both run on the A10; ground truth and OCR come from
the Titan DB (`correctedValue` + decrypted OCR); all verification runs locally.

- **Prediction** = the extractor's output (NuExtract field values / MinerU table HTML).
- **Ground truth** = `correctedValue` (human-verified) for fields; vision-adjudicated GOOD/BAD for tables.
- **Correctness (fields)** = normalized bidirectional containment of prediction vs GT.
- Verifier evidence (no extra generative call): source-grounding (value-in-OCR), format, emptiness
  + field empty-prior; **ROI spatial grounding** (predicted value vs GT bbox/tokens) for the
  structured forms; Table-Trust structural score + independent docTR witness for tables.

## Fields — both field modes, all 5 document types
NuExtract is a mid-tier extractor, so it makes many errors on these hard mortgage documents
(17–43% field error rate) — i.e. **thousands of real errors**, far more than the public
benchmarks, which makes this a well-powered test. CV-fused verifier (GroupKFold by document):

| Doc type | Mode | n fields | errors (rate) | **AUROC** | coverage @≤5% risk |
|---|---|---|---|---|---|
| URLA (Form 1003) | Structured / ROI | 5970 | 1018 (17.1%) | **0.950** | 86% |
| CD (Closing Disclosure) | Structured / ROI | 3300 | 574 (17.4%) | **0.947** | 81% |
| AUS_DU (Desktop Underwriter) | Unstructured / Signal | 5970 | 1602 (26.8%) | **0.994** | 75% |
| Bank statements | Unstructured / Signal | 1330 | 567 (42.6%) | **0.941** | 2% |
| Credit report | Unstructured / Signal | 3204 | 1133 (35.4%) | **0.930** | 34% |

Takeaways:
- The verifier catches extractor errors at **AUROC 0.93–0.99** across both structured and
  unstructured field modes, on a proprietary dataset it was not tuned for.
- Coverage tracks the error rate: where NuExtract is very wrong (Bank 42.6%), little can be
  auto-accepted at ≤5% risk even though ranking (AUROC) stays strong — the honest capability axis.

(Source: `results/rocket_preds/rocket_fields_summary.json`.)

## Tables — Table-Trust on MinerU tables, three domains
105 MinerU tables (CD 45, Bank 30, Credit report 30) scored by Table-Trust (structural signals +
an independent docTR witness run on the **cropped table**). **Ground truth = blind 2-annotator**
(two different models) + author adjudication under a stated fidelity rubric.

**Witness note:** the witness must be docTR on the *cropped table*, not the full page — the
full-page witness caused false `LOW_TEXT_RECALL`; the crop restores text-recall to ~0.99.
**Annotation note:** on the bank/credit tables the two annotators split on one family — MinerU
fuses credit late-counts ("30/0" → "**300**", "60/1" → "601"), which loses the separator and can
hide a real late payment (κ=0.23). Adjudicated rubric: **fused / truncated / dropped values =
defect** → those are BAD.

| Domain | n | BAD | bad-catch @ trust<85 | false-reject | AUROC |
|---|---|---|---|---|---|
| CD | 45 | 4 | 0.75 | 0.22 | 0.78 |
| Bank | 30 | 10 | 0.80 | 0.45 | 0.74 |
| Credit report | 30 | 20 | **1.00** | 0.60 | 0.71 |
| **Combined** | **105** | **34** | **0.91** | 0.34 | **0.825** |

Takeaways:
- **The verifier catches 31/34 real table defects (0.91)** — the fusions, truncations
  (12→11-month pay patterns) and dropped rows MinerU makes on dense bank/credit tables.
- **Honest boundary: false-reject 0.34** — Table-Trust over-rejects atypical layouts (blank
  reconciliation forms, flattened-but-correct dumps), most on credit reports (0.60). A real
  deployment lesson, not hidden.
- Headline hard-tail example: CD idx 22 **drops the loan-type checkboxes** but keeps a valid grid
  → **trust 100, a confident miss** — a concrete *"hard error that looks right."*
- The **blinded 2-annotator + rubric adjudication** (κ reported) answers the review's
  annotation-rigor concern.
- The cleaner, larger quantitative tables *benchmark* remains **RD-TableBench**; ROCKET tables are
  the real-deployment, cross-domain check with abundant natural defects.

(Sources: `results/rocket_preds/rocket_tables_summary.json`; labels + crops retained for audit.)

## What this adds to the paper
A **proprietary, real-world deployment** result showing the single verifier works end-to-end
across structured fields, unstructured fields, and tables on the **same** document pool —
directly supporting the unified-system framing, with a mid-tier extractor supplying abundant
natural errors.
