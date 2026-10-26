# Direct NTP Binary Classifier — Results

The model takes 7 signal values and directly classifies each field as
**NTP** (auto-accept) or **Review** (needs human check). No thresholding.

---

## s1_filing

### Field-Level NTP

| Method | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught | Review Rate |
|--------|----------|-------------|----------------|---------------|-------------|
| current_system_t0.3 | 99.8% | 95.2% | 7053 | 139 (1.9%) | 0.2% |
| current_system_t0.5 | 97.4% | 97.1% | 4232 | 2960 (41.2%) | 2.6% |
| current_system_t0.7 | 0.6% | 79.0% | 194 | 6998 (97.3%) | 99.4% |
| rf | 93.7% | 99.7% | 440 | 6752 (93.9%) | 6.3% |
| gbm | 93.7% | 99.7% | 451 | 6741 (93.7%) | 6.3% |
| current_system_matched_t0.495 | 97.4% | 97.1% | 4232 | 2960 (41.2%) | 2.6% |

### Document-Level NTP

A document is NTP only if ALL its fields are NTP.

| Method | Doc NTP Rate | Doc NTP Accuracy | Doc Errors Escaped | Doc Errors Caught |
|--------|-------------|-----------------|-------------------|-------------------|
| current_system_t0.3 | 97.1% | 4.9% | 5834 | 165 (2.8%) |
| current_system_t0.5 | 57.9% | 3.6% | 3529 | 2470 (41.2%) |
| current_system_t0.7 | 0.0% | 0% | 0 | 5999 (100.0%) |
| rf | 0.2% | 0.0% | 10 | 5989 (99.8%) |
| gbm | 0.2% | 0.0% | 11 | 5988 (99.8%) |

### CV Stability (per-fold NTP metrics)

- **rf**: NTP rate 93.7% +/- 0.2%, accuracy 99.7% +/- 0.0%, error catch 93.9% +/- 0.7%
- **gbm**: NTP rate 93.7% +/- 0.1%, accuracy 99.7% +/- 0.0%, error catch 93.7% +/- 0.7%

### Held-Out Test Set

| Model | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught |
|-------|----------|-------------|----------------|---------------|
| rf | 93.7% | 99.7% | 77 | 1361 (94.6%) |
| gbm | 93.7% | 99.7% | 79 | 1359 (94.5%) |

---

## Summary: Best ML Model Per Doc Type

| Doc Type | Model | NTP Rate | NTP Accuracy | Error Catch Rate |
|----------|-------|----------|-------------|------------------|
| s1_filing | rf | 93.7% | 99.7% | 93.9% |
