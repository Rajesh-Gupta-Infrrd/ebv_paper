# Direct NTP Binary Classifier — Results

The model takes 7 signal values and directly classifies each field as
**NTP** (auto-accept) or **Review** (needs human check). No thresholding.

---

## charity_report

### Field-Level NTP

| Method | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught | Review Rate |
|--------|----------|-------------|----------------|---------------|-------------|
| current_system_t0.3 | 97.6% | 72.2% | 1960 | 116 (5.6%) | 2.4% |
| current_system_t0.5 | 80.8% | 76.4% | 1378 | 698 (33.6%) | 19.2% |
| current_system_t0.7 | 28.4% | 77.7% | 456 | 1620 (78.0%) | 71.6% |
| rf | 61.0% | 90.0% | 439 | 1637 (78.9%) | 39.0% |
| gbm | 61.2% | 89.7% | 457 | 1619 (78.0%) | 38.8% |
| current_system_matched_t0.501 | 57.9% | 71.9% | 1173 | 903 (43.5%) | 42.1% |

### Document-Level NTP

A document is NTP only if ALL its fields are NTP.

| Method | Doc NTP Rate | Doc NTP Accuracy | Doc Errors Escaped | Doc Errors Caught |
|--------|-------------|-----------------|-------------------|-------------------|
| current_system_t0.3 | 51.6% | 1.5% | 131 | 125 (48.8%) |
| current_system_t0.5 | 2.7% | 28.6% | 5 | 251 (98.0%) |
| current_system_t0.7 | 0.0% | 0% | 0 | 256 (100.0%) |
| rf | 0.4% | 100.0% | 0 | 256 (100.0%) |
| gbm | 0.4% | 100.0% | 0 | 256 (100.0%) |

### CV Stability (per-fold NTP metrics)

- **rf**: NTP rate 61.0% +/- 0.9%, accuracy 90.1% +/- 0.8%, error catch 78.8% +/- 1.6%
- **gbm**: NTP rate 61.2% +/- 1.2%, accuracy 89.7% +/- 0.8%, error catch 78.0% +/- 1.8%

### Held-Out Test Set

| Model | NTP Rate | NTP Accuracy | Errors Escaped | Errors Caught |
|-------|----------|-------------|----------------|---------------|
| rf | 61.0% | 88.4% | 102 | 313 (75.4%) |
| gbm | 62.8% | 88.0% | 109 | 306 (73.7%) |

---

## Summary: Best ML Model Per Doc Type

| Doc Type | Model | NTP Rate | NTP Accuracy | Error Catch Rate |
|----------|-------|----------|-------------|------------------|
| charity_report | rf | 61.0% | 90.0% | 78.9% |
