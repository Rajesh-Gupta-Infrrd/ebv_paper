# Direct NTP Binary Classifier — Results

The model takes 7 signal values and directly classifies each field as
**NTP** (auto-accept) or **Review** (needs human check). No thresholding.

---

## invoice

### Field-Level NTP

| Method | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught | Review Rate |
|--------|----------|-------------|----------------|---------------|-------------|
| current_system_t0.3 | 97.4% | 68.2% | 556 | 44 (7.3%) | 2.6% |
| current_system_t0.5 | 88.9% | 70.1% | 477 | 123 (20.5%) | 11.1% |
| current_system_t0.7 | 36.0% | 89.2% | 70 | 530 (88.3%) | 64.0% |
| rf | 56.7% | 89.5% | 107 | 493 (82.2%) | 43.3% |
| gbm | 58.1% | 89.4% | 110 | 490 (81.7%) | 41.9% |
| current_system_matched_t0.572 | 56.9% | 78.1% | 224 | 376 (62.7%) | 43.1% |

### Document-Level NTP

A document is NTP only if ALL its fields are NTP.

| Method | Doc NTP Rate | Doc NTP Accuracy | Doc Errors Escaped | Doc Errors Caught |
|--------|-------------|-----------------|-------------------|-------------------|
| current_system_t0.3 | 90.9% | 3.8% | 153 | 16 (9.5%) |
| current_system_t0.5 | 41.1% | 5.6% | 68 | 101 (59.8%) |
| current_system_t0.7 | 0.0% | 0% | 0 | 169 (100.0%) |
| rf | 0.0% | 0% | 0 | 169 (100.0%) |
| gbm | 0.0% | 0% | 0 | 169 (100.0%) |

### CV Stability (per-fold NTP metrics)

- **rf**: NTP rate 56.7% +/- 1.7%, accuracy 89.5% +/- 2.0%, error catch 82.2% +/- 3.7%
- **gbm**: NTP rate 58.1% +/- 2.4%, accuracy 89.5% +/- 2.3%, error catch 81.7% +/- 4.4%

### Held-Out Test Set

| Model | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught |
|-------|----------|-------------|----------------|---------------|
| rf | 58.2% | 86.6% | 28 | 92 (76.7%) |
| gbm | 61.0% | 85.8% | 31 | 89 (74.2%) |

---

## Summary: Best ML Model Per Doc Type

| Doc Type | Model | NTP Rate | NTP Accuracy | Error Catch Rate |
|----------|-------|----------|-------------|------------------|
| invoice | rf | 56.7% | 89.5% | 82.2% |
