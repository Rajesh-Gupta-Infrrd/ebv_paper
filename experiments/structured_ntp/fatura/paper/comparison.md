# Structured (ROI) NTP — v2 results (all layers ON)

All runs drive NTP's **full** production pipeline offline (no Mongo):
`compute_roi_for_doc_type` (geometry + per-field thresholds + contextKeywords) →
`calibrate_from_evaluation_dataframes` (grid-searched weights + score threshold) →
`evaluate_doc_type` (keyword-context boost + empty-field handling + per-field thresholds).
50 FATURA templates, per-template 70/30 split (7000 train / 3000 test), seed 42.

## Headline comparison (field-level, operating point = calibrated per field)
| task | ROI learned from | correctness | n | error rate | error-catch | false-alarm | route-prec | AURC |
|---|---|---|---|---|---|---|---|---|
| **1** | correct predictions | **containment** | 36,370 | 24.2% | **0.9999** | 0.039 | 0.892 | 0.0001 |
| **3a** | correct predictions | **exact** (clean GT) | 38,549 | 33.7% | **0.829** | 0.045 | 0.904 | 0.0097 |
| **3b** | **clean GT (production)** | **exact** | 38,549 | 33.7% | **0.811** | 0.087 | 0.826 | 0.0091 |

Document-level (accept iff all units accept):
| task | error docs | doc error-catch | doc false-alarm |
|---|---|---|---|
| 1 | 2,837 | 1.000 | 0.736 |
| 3a | 2,934 | 0.998 | 0.667 |
| 3b | 2,934 | 0.999 | 0.818 |

## What the comparison shows (honest reading)
1. **Enabling calibration/keyword/empty barely moved the containment result** (Task 1 ≈ the earlier defaults run: ~99.99% catch). When errors are gross mislocations/hallucinations, the extra layers don't change the verdict.
2. **Exact vs containment is THE driver.** Under exact matching (3a/3b) the ROI verifier catches ~81–83% of errors, not ~100%. The ~17–19% it misses are **in-place value/formatting errors** — right location, wrong value (e.g. a wrong digit in the correct cell) — which spatial verification cannot catch *by design*. This is the genuine **detectability frontier** for the structured/ROI channel.
3. **Prediction-based ROI (3a) ≈ production GT-based ROI (3b).** Catch 0.829 vs 0.811; and the prediction-ROI has *lower* false-alarm (0.045 vs 0.087) because the region is aligned to where this extractor actually places correct values. So the "learn from correct predictions" workaround is a faithful — even slightly better-calibrated — proxy for the GT-based production ROI. Either is defensible; production uses GT.
4. **Document-level false-alarm is high (67–82%)** because ~98% of FATURA docs contain ≥1 exact-error (mostly the hard fields TOTAL_WORDS / NUMBER / CONDITIONS), so almost every document routes. This is the real usability cost of document-level "accept iff all units accept" on this data.

## Task 2 — GT cleaning (enabler for exact / 3a / 3b)
FATURA GT bundles label+value+unit. A **field-type-aware** cleaner (strip label; AMOUNT→numeric
magnitude; keep multi-line blocks) recovers pure values. Validation vs NuExtract predictions with
NTP's own field-aware matcher: **exact-match 89.7%, containment 94.0%, agreement 94.0%**. Residual
exact<containment gap is concentrated in long free-text/ID fields (CONDITIONS, SEND_TO, NUMBER,
TOTAL_WORDS) where exact is legitimately stricter — not cleaning bugs. Verdict: **good to run
end-to-end with exact matching**, noting exact reports higher error on long-text fields.
(Full per-field quality: `gt_clean/cleaning_quality.json`.)
