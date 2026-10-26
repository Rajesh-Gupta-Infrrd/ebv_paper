# Direct NTP Binary Classifier — Results

The model takes 7 signal values and directly classifies each field as
**NTP** (auto-accept) or **Review** (needs human check). No thresholding.

---

## nda

### Field-Level NTP

| Method | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught | Review Rate |
|--------|----------|-------------|----------------|---------------|-------------|
| current_system_t0.3 | 90.9% | 71.5% | 154 | 48 (23.8%) | 9.1% |
| current_system_t0.5 | 62.8% | 67.6% | 121 | 81 (40.1%) | 37.2% |
| current_system_t0.7 | 22.4% | 66.9% | 44 | 158 (78.2%) | 77.6% |
| rf | 62.8% | 86.6% | 50 | 152 (75.2%) | 37.2% |
| gbm | 63.5% | 87.5% | 47 | 155 (76.7%) | 36.5% |
| current_system_matched_t0.474 | 63.0% | 67.6% | 121 | 81 (40.1%) | 37.0% |

### Document-Level NTP

A document is NTP only if ALL its fields are NTP.

| Method | Doc NTP Rate | Doc NTP Accuracy | Doc Errors Escaped | Doc Errors Caught |
|--------|-------------|-----------------|-------------------|-------------------|
| current_system_t0.3 | 73.7% | 32.9% | 98 | 49 (33.3%) |
| current_system_t0.5 | 20.2% | 27.5% | 29 | 118 (80.3%) |
| current_system_t0.7 | 0.0% | 0% | 0 | 147 (100.0%) |
| rf | 9.1% | 61.1% | 7 | 140 (95.2%) |
| gbm | 11.1% | 54.5% | 10 | 137 (93.2%) |

### CV Stability (per-fold NTP metrics)

- **rf**: NTP rate 62.8% +/- 3.7%, accuracy 86.7% +/- 2.5%, error catch 75.3% +/- 5.7%
- **gbm**: NTP rate 63.4% +/- 1.4%, accuracy 87.6% +/- 2.6%, error catch 76.7% +/- 5.1%

### Held-Out Test Set

| Model | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught |
|-------|----------|-------------|----------------|---------------|
| rf | 62.2% | 82.4% | 13 | 27 (67.5%) |
| gbm | 62.2% | 82.4% | 13 | 27 (67.5%) |

---

## Summary: Best ML Model Per Doc Type

| Doc Type | Model | NTP Rate | NTP Accuracy | Error Catch Rate |
|----------|-------|----------|-------------|------------------|
| nda | gbm | 63.5% | 87.5% | 76.7% |
