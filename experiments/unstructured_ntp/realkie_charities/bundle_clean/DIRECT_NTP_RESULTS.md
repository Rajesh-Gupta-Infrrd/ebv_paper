# Direct NTP Binary Classifier — Results

The model takes 7 signal values and directly classifies each field as
**NTP** (auto-accept) or **Review** (needs human check). No thresholding.

---

## charity_report

### Field-Level NTP

| Method | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught | Review Rate |
|--------|----------|-------------|----------------|---------------|-------------|
| current_system_t0.3 | 97.8% | 83.1% | 1035 | 83 (7.4%) | 2.2% |
| current_system_t0.5 | 82.6% | 86.1% | 719 | 399 (35.7%) | 17.4% |
| current_system_t0.7 | 30.0% | 84.9% | 284 | 834 (74.6%) | 70.0% |
| rf | 68.3% | 93.8% | 265 | 853 (76.3%) | 31.7% |
| gbm | 68.6% | 93.7% | 270 | 848 (75.8%) | 31.4% |
| current_system_matched_t0.501 | 57.7% | 83.3% | 605 | 513 (45.9%) | 42.3% |

### Document-Level NTP

A document is NTP only if ALL its fields are NTP.

| Method | Doc NTP Rate | Doc NTP Accuracy | Doc Errors Escaped | Doc Errors Caught |
|--------|-------------|-----------------|-------------------|-------------------|
| current_system_t0.3 | 59.7% | 7.1% | 143 | 103 (41.9%) |
| current_system_t0.5 | 7.4% | 26.3% | 14 | 232 (94.3%) |
| current_system_t0.7 | 0.0% | 0% | 0 | 246 (100.0%) |
| rf | 0.0% | 0% | 0 | 246 (100.0%) |
| gbm | 0.0% | 0% | 0 | 246 (100.0%) |

### CV Stability (per-fold NTP metrics)

- **rf**: NTP rate 68.3% +/- 1.0%, accuracy 93.8% +/- 0.7%, error catch 76.3% +/- 2.6%
- **gbm**: NTP rate 68.6% +/- 1.3%, accuracy 93.7% +/- 0.4%, error catch 75.8% +/- 1.3%

### Held-Out Test Set

| Model | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught |
|-------|----------|-------------|----------------|---------------|
| rf | 70.7% | 92.4% | 67 | 157 (70.1%) |
| gbm | 70.0% | 91.9% | 71 | 153 (68.3%) |

---

## Summary: Best ML Model Per Doc Type

| Doc Type | Model | NTP Rate | NTP Accuracy | Error Catch Rate |
|----------|-------|----------|-------------|------------------|
| charity_report | rf | 68.3% | 93.8% | 76.3% |
