# Direct NTP Binary Classifier — Results

The model takes 7 signal values and directly classifies each field as
**NTP** (auto-accept) or **Review** (needs human check). No thresholding.

---

## nda

### Field-Level NTP

| Method | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught | Review Rate |
|--------|----------|-------------|----------------|---------------|-------------|
| current_system_t0.3 | 90.8% | 72.8% | 144 | 48 (25.0%) | 9.2% |
| current_system_t0.5 | 62.3% | 69.2% | 112 | 80 (41.7%) | 37.7% |
| current_system_t0.7 | 22.4% | 67.9% | 42 | 150 (78.1%) | 77.6% |
| rf | 64.6% | 87.3% | 48 | 144 (75.0%) | 35.4% |
| gbm | 63.0% | 88.3% | 43 | 149 (77.6%) | 37.0% |
| current_system_matched_t0.474 | 62.5% | 69.3% | 112 | 80 (41.7%) | 37.5% |

### Document-Level NTP

A document is NTP only if ALL its fields are NTP.

| Method | Doc NTP Rate | Doc NTP Accuracy | Doc Errors Escaped | Doc Errors Caught |
|--------|-------------|-----------------|-------------------|-------------------|
| current_system_t0.3 | 73.7% | 35.6% | 94 | 49 (34.3%) |
| current_system_t0.5 | 20.2% | 30.0% | 28 | 115 (80.4%) |
| current_system_t0.7 | 0.0% | 0% | 0 | 143 (100.0%) |
| rf | 14.1% | 60.7% | 11 | 132 (92.3%) |
| gbm | 12.6% | 56.0% | 11 | 132 (92.3%) |

### CV Stability (per-fold NTP metrics)

- **rf**: NTP rate 64.6% +/- 4.4%, accuracy 87.4% +/- 2.3%, error catch 75.0% +/- 6.2%
- **gbm**: NTP rate 63.0% +/- 3.1%, accuracy 88.4% +/- 1.7%, error catch 77.6% +/- 4.1%

### Held-Out Test Set

| Model | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught |
|-------|----------|-------------|----------------|---------------|
| rf | 64.1% | 86.7% | 10 | 28 (73.7%) |
| gbm | 65.8% | 84.4% | 12 | 26 (68.4%) |

---

## Summary: Best ML Model Per Doc Type

| Doc Type | Model | NTP Rate | NTP Accuracy | Error Catch Rate |
|----------|-------|----------|-------------|------------------|
| nda | gbm | 63.0% | 88.3% | 77.6% |
