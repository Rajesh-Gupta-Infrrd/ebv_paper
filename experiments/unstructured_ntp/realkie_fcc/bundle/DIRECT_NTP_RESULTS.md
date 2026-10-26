# Direct NTP Binary Classifier — Results

The model takes 7 signal values and directly classifies each field as
**NTP** (auto-accept) or **Review** (needs human check). No thresholding.

---

## invoice

### Field-Level NTP

| Method | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught | Review Rate |
|--------|----------|-------------|----------------|---------------|-------------|
| current_system_t0.3 | 97.4% | 63.7% | 681 | 49 (6.7%) | 2.6% |
| current_system_t0.5 | 87.9% | 66.0% | 575 | 155 (21.2%) | 12.1% |
| current_system_t0.7 | 35.0% | 85.2% | 100 | 630 (86.3%) | 65.0% |
| rf | 56.9% | 84.9% | 166 | 564 (77.3%) | 43.1% |
| gbm | 56.7% | 85.3% | 160 | 570 (78.1%) | 43.3% |
| current_system_matched_t0.572 | 56.2% | 73.7% | 285 | 445 (61.0%) | 43.8% |

### Document-Level NTP

A document is NTP only if ALL its fields are NTP.

| Method | Doc NTP Rate | Doc NTP Accuracy | Doc Errors Escaped | Doc Errors Caught |
|--------|-------------|-----------------|-------------------|-------------------|
| current_system_t0.3 | 88.0% | 0.6% | 153 | 21 (12.1%) |
| current_system_t0.5 | 36.6% | 1.6% | 63 | 111 (63.8%) |
| current_system_t0.7 | 0.0% | 0% | 0 | 174 (100.0%) |
| rf | 0.0% | 0% | 0 | 174 (100.0%) |
| gbm | 0.0% | 0% | 0 | 174 (100.0%) |

### CV Stability (per-fold NTP metrics)

- **rf**: NTP rate 56.9% +/- 1.5%, accuracy 84.9% +/- 1.2%, error catch 77.3% +/- 2.3%
- **gbm**: NTP rate 56.7% +/- 1.2%, accuracy 85.4% +/- 1.7%, error catch 78.1% +/- 2.8%

### Held-Out Test Set

| Model | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught |
|-------|----------|-------------|----------------|---------------|
| rf | 54.5% | 87.1% | 27 | 119 (81.5%) |
| gbm | 55.3% | 85.9% | 30 | 116 (79.5%) |

---

## Summary: Best ML Model Per Doc Type

| Doc Type | Model | NTP Rate | NTP Accuracy | Error Catch Rate |
|----------|-------|----------|-------------|------------------|
| invoice | gbm | 56.7% | 85.3% | 78.1% |
