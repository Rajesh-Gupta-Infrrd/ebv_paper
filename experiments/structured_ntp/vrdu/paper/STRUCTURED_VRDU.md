# Structured (ROI) NTP — VRDU robustness results

Same NTP spatial ROI pipeline as the FATURA leg (no extra LLM/VLM call), on **VRDU
Registration-Forms (FARA)**: **1,915 REAL documents**, 3 form templates (Short-Form 789,
Amendment 709, Dissemination Report 417), 6 fields, per-field boxes. Extractor = NuExtract-3.
Per-template 70/30 split (seed 42): 1,340 train / 575 test. ROI geometry/evaluate driven offline
via NTP's venv; OCR token boxes come from VRDU's `dataset.jsonl` (no page images needed).
This is the **real-document counterpart to synthetic FATURA** for the structured channel.

## Versions & axes (identical to the FATURA leg)
v1 pred-ROI/calib-OFF · v2 pred-ROI/calib-ON · v3 GT-ROI/calib-ON (production) · v4 GT-ROI/calib-OFF.
Correctness is a LABEL on the same accept/route decisions: `exact` = NTP field-aware matcher on
cleaned GT; `containment` = normalized substring (lenient). Population: `present` = fields in the
doc's GT (honest spatial task); `full` = + absent-field hallucinations (trivially routed).
VRDU GT can be multi-value → correctness = prediction matches ANY GT occurrence.

## RESULTS — present-field population (honest spatial-detectability)
| ver | config | correctness | n | err-rate | error-catch ↑ | false-alarm ↓ | route-prec ↑ | accuracy ↑ | AURC ↓ |
|---|---|---|---|---|---|---|---|---|---|
| v1 | pred-ROI, calib OFF | exact | 2647 | 0.206 | 0.7831 | 0.2701 | 0.4286 | 0.7408 | 0.0477 |
| v1 | pred-ROI, calib OFF | containment | 2647 | 0.216 | 0.7968 | 0.2596 | 0.4577 | 0.7526 | 0.0453 |
| v2 | pred-ROI, calib ON | exact | 2647 | 0.206 | 0.4871 | 0.0856 | 0.5955 | 0.8266 | 0.1431 |
| v2 | pred-ROI, calib ON | containment | 2647 | 0.216 | 0.5236 | 0.0670 | 0.6826 | 0.8447 | 0.1063 |
| v3 | GT-ROI, calib ON (prod) | exact | 2647 | 0.206 | 0.7500 | 0.0861 | 0.6927 | 0.8802 | 0.0276 |
| v3 | GT-ROI, calib ON (prod) | containment | 2647 | 0.216 | 0.7811 | 0.0665 | 0.7637 | 0.9006 | 0.0178 |
| v4 | GT-ROI, calib OFF | exact | 2647 | 0.206 | 0.9228 | 0.2630 | 0.4758 | 0.7752 | 0.0242 |
| v4 | GT-ROI, calib OFF | containment | 2647 | 0.216 | 0.9492 | 0.2471 | 0.5137 | 0.7952 | 0.0181 |

## RESULTS — full population (includes absent-field hallucinations)
| ver | config | correctness | n | err-rate | error-catch ↑ | false-alarm ↓ | route-prec ↑ | accuracy ↑ | AURC ↓ |
|---|---|---|---|---|---|---|---|---|---|
| v1 | pred-ROI, calib OFF | exact | 3015 | 0.302 | 0.8026 | 0.2701 | 0.5631 | 0.7519 | 0.0756 |
| v1 | pred-ROI, calib OFF | containment | 3015 | 0.311 | 0.8104 | 0.2596 | 0.5854 | 0.7622 | 0.0733 |
| v2 | pred-ROI, calib ON | exact | 3015 | 0.302 | 0.6283 | 0.0856 | 0.7610 | 0.8279 | 0.1597 |
| v2 | pred-ROI, calib ON | containment | 3015 | 0.311 | 0.6464 | 0.0670 | 0.8137 | 0.8438 | 0.1258 |
| v3 | GT-ROI, calib ON (prod) | exact | 3015 | 0.302 | 0.7643 | 0.0861 | 0.7938 | 0.8687 | 0.0592 |
| v3 | GT-ROI, calib ON (prod) | containment | 3015 | 0.311 | 0.7859 | 0.0665 | 0.8425 | 0.8876 | 0.0510 |
| v4 | GT-ROI, calib OFF | exact | 3015 | 0.302 | 0.8827 | 0.2630 | 0.5928 | 0.7811 | 0.0605 |
| v4 | GT-ROI, calib OFF | containment | 3015 | 0.311 | 0.8999 | 0.2471 | 0.6222 | 0.7987 | 0.0547 |
*(↑ higher better, ↓ lower better.)*

## Per-field breakdown — production config v3 (GT-ROI, calib ON), present/exact
| field | n | err-rate | error-catch ↑ | false-alarm ↓ | accuracy ↑ |
|---|---|---|---|---|---|
| file_date | 560 | 0.739 | 0.778 | 0.178 | 0.789 |
| foreign_principle_name | 345 | 0.046 | 0.750 | 0.082 | 0.910 |
| registrant_name | 575 | 0.066 | 0.763 | 0.074 | 0.915 |
| registration_num | 572 | 0.024 | 0.929 | 0.088 | 0.913 |
| signer_name | 432 | 0.113 | 0.612 | 0.063 | 0.900 |
| signer_title | 163 | 0.080 | 0.154 | 0.100 | 0.840 |

> Note: NuExtract reformats dates to ISO (e.g. `2008-07-17`) which is not verbatim in the page
> OCR, so `file_date`'s predicted value is harder to localize spatially than the other fields —
> report it separately, as flagged in the data-provenance analysis.

## Data provenance
Predictions + GT: `experiments/results/vrdu_results/`. OCR token boxes + split + clean GT produced by
`scripts/prep_vrdu_roi.py` from `vrdu/registration-form/main/dataset.jsonl`
(`structured_ntp/inputs/vrdu_ocr/`, `structured_ntp/splits/vrdu_split.json`,
`gt_clean/ground_truth_vrdu_clean.json`). Matrix decisions under `matrix/vrdu_*`.
