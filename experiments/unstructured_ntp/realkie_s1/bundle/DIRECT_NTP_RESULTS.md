# Direct NTP Binary Classifier — Results

The model takes 7 signal values and directly classifies each field as
**NTP** (auto-accept) or **Review** (needs human check). No thresholding.

---

## s1_filing

### Field-Level NTP

| Method | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught | Review Rate |
|--------|----------|-------------|----------------|---------------|-------------|
| current_system_t0.3 | 99.6% | 93.6% | 9691 | 413 (4.1%) | 0.4% |
| current_system_t0.5 | 96.8% | 95.8% | 6243 | 3861 (38.2%) | 3.2% |
| current_system_t0.7 | 1.0% | 47.6% | 803 | 9301 (92.1%) | 99.0% |
| rf | 91.6% | 99.7% | 441 | 9663 (95.6%) | 8.4% |
| gbm | 91.6% | 99.7% | 443 | 9661 (95.6%) | 8.4% |
| current_system_matched_t0.495 | 96.8% | 95.8% | 6243 | 3861 (38.2%) | 3.2% |

### Document-Level NTP

A document is NTP only if ALL its fields are NTP.

| Method | Doc NTP Rate | Doc NTP Accuracy | Doc Errors Escaped | Doc Errors Caught |
|--------|-------------|-----------------|-------------------|-------------------|
| current_system_t0.3 | 93.4% | 3.3% | 5707 | 410 (6.7%) |
| current_system_t0.5 | 55.9% | 2.7% | 3436 | 2681 (43.8%) |
| current_system_t0.7 | 0.0% | 0% | 0 | 6117 (100.0%) |
| rf | 0.0% | 0% | 0 | 6117 (100.0%) |
| gbm | 0.0% | 0% | 0 | 6117 (100.0%) |

### CV Stability (per-fold NTP metrics)

- **rf**: NTP rate 91.6% +/- 0.1%, accuracy 99.7% +/- 0.0%, error catch 95.6% +/- 0.2%
- **gbm**: NTP rate 91.5% +/- 0.1%, accuracy 99.7% +/- 0.0%, error catch 95.6% +/- 0.2%

### Held-Out Test Set

| Model | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught |
|-------|----------|-------------|----------------|---------------|
| rf | 91.8% | 99.7% | 92 | 1929 (95.4%) |
| gbm | 91.7% | 99.7% | 92 | 1929 (95.4%) |

---

## Summary: Best ML Model Per Doc Type

| Doc Type | Model | NTP Rate | NTP Accuracy | Error Catch Rate |
|----------|-------|----------|-------------|------------------|
| s1_filing | rf | 91.6% | 99.7% | 95.6% |
