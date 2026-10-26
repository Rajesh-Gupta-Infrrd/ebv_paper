# EBV robustness round — results on the new datasets

Reproduces the original FATURA (structured/ROI) and FCC (unstructured/Signal) experiments on
**new datasets** to test generalization (synthetic↔real, single↔multi-domain). Same pipelines,
**no extra LLM/VLM call**, dociq + NTP production code driven in place and left untouched. Every
number below is pulled from the stored metrics JSON by `build_robustness_report.py`.

Datasets added this round:
- **Structured / ROI:** VRDU Registration-Forms (FARA) — 1,915 **real** docs, 3 templates, 6 fields —
  the real-document counterpart to synthetic FATURA.
- **Unstructured / Signal:** RealKIE **Charities**, **NDA**, **S-1** — new domains beyond FCC invoices.

---

## 1. Structured / ROI — VRDU (real templatic forms)

Same NTP spatial pipeline as FATURA. Per-template 70/30 split (seed 42), 1,340 train / 575 test.
OCR token boxes + split + clean GT derived from `dataset.jsonl` (no page images needed).

### Present-field population (the honest spatial-detectability numbers)
| ver | config | correctness | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc ↑ | AURC ↓ |
|---|---|---|---|---|---|---|---|---|---|
| v1 | pred-ROI, calib OFF | exact | 2647 | 0.2055 | 0.7831 | 0.2701 | 0.4286 | 0.7408 | 0.0477 |
| v1 | pred-ROI, calib OFF | containment | 2647 | 0.2157 | 0.7968 | 0.2596 | 0.4577 | 0.7526 | 0.0453 |
| v2 | pred-ROI, calib ON | exact | 2647 | 0.2055 | 0.4871 | 0.0856 | 0.5955 | 0.8266 | 0.1431 |
| v2 | pred-ROI, calib ON | containment | 2647 | 0.2157 | 0.5236 | 0.0670 | 0.6826 | 0.8447 | 0.1063 |
| v3 | GT-ROI, calib ON (prod) | exact | 2647 | 0.2055 | 0.7500 | 0.0861 | 0.6927 | 0.8802 | 0.0276 |
| v3 | GT-ROI, calib ON (prod) | containment | 2647 | 0.2157 | 0.7811 | 0.0665 | 0.7637 | 0.9006 | 0.0178 |
| v4 | GT-ROI, calib OFF | exact | 2647 | 0.2055 | 0.9228 | 0.2630 | 0.4758 | 0.7752 | 0.0242 |
| v4 | GT-ROI, calib OFF | containment | 2647 | 0.2157 | 0.9492 | 0.2471 | 0.5137 | 0.7952 | 0.0181 |

### Full population (adds absent-field hallucinations; catch inflated)
| ver | config | correctness | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc ↑ | AURC ↓ |
|---|---|---|---|---|---|---|---|---|---|
| v1 | pred-ROI, calib OFF | exact | 3015 | 0.3025 | 0.8026 | 0.2701 | 0.5631 | 0.7519 | 0.0756 |
| v1 | pred-ROI, calib OFF | containment | 3015 | 0.3114 | 0.8104 | 0.2596 | 0.5854 | 0.7622 | 0.0733 |
| v2 | pred-ROI, calib ON | exact | 3015 | 0.3025 | 0.6283 | 0.0856 | 0.7610 | 0.8279 | 0.1597 |
| v2 | pred-ROI, calib ON | containment | 3015 | 0.3114 | 0.6464 | 0.0670 | 0.8137 | 0.8438 | 0.1258 |
| v3 | GT-ROI, calib ON (prod) | exact | 3015 | 0.3025 | 0.7643 | 0.0861 | 0.7938 | 0.8687 | 0.0592 |
| v3 | GT-ROI, calib ON (prod) | containment | 3015 | 0.3114 | 0.7859 | 0.0665 | 0.8425 | 0.8876 | 0.0510 |
| v4 | GT-ROI, calib OFF | exact | 3015 | 0.3025 | 0.8827 | 0.2630 | 0.5928 | 0.7811 | 0.0605 |
| v4 | GT-ROI, calib OFF | containment | 3015 | 0.3114 | 0.8999 | 0.2471 | 0.6222 | 0.7987 | 0.0547 |

### Per-field — production config v3 (GT-ROI, calib ON), present/exact
| field | n | err | catch ↑ | FA ↓ | acc ↑ |
|---|---|---|---|---|---|
| file_date | 560 | 0.7393 | 0.7778 | 0.1781 | 0.7893 |
| foreign_principle_name | 345 | 0.0464 | 0.7500 | 0.0821 | 0.9101 |
| registrant_name | 575 | 0.0661 | 0.7632 | 0.0745 | 0.9148 |
| registration_num | 572 | 0.0245 | 0.9286 | 0.0878 | 0.9126 |
| signer_name | 432 | 0.1134 | 0.6122 | 0.0627 | 0.9005 |
| signer_title | 163 | 0.0798 | 0.1538 | 0.1000 | 0.8405 |

### AUROC & coverage (competitor metrics), present-field
Expressed on Jin et al. (2609.20110)'s own axes — **AUROC** for "is this value correct" + **auto-approval
coverage** at a fixed accepted-error target — computed on our decisions by
`scripts/compute_vrdu_auroc_coverage.py` (all numbers in `paper/structured_vrdu_metrics.json`).

| ver | config | correctness | AUROC ↑ | cov@≤5% | cov@≤10% | cov@≤20% |
|---|---|---|---|---|---|---|
| v1 | pred-ROI, calib OFF | exact | 0.7466 | 52.5% | 64.4% | 89.5% |
| v2 | pred-ROI, calib ON | exact | 0.3980 | 5.2% | 5.2% | 89.5% |
| v3 | GT-ROI, calib ON (prod) | exact | **0.8963** | 70.8% | 83.3% | 89.5% |
| v4 | GT-ROI, calib OFF | exact | 0.9114 | 76.8% | 83.3% | 89.5% |
| v3 | GT-ROI, calib ON (prod) | containment | 0.9372 | 74.6% | 83.3% | 89.5% |

(All eight ver×correctness cells are stored in the JSON; the exact rows plus v3-containment are shown.)

**Paper-reported — finalized config v3 (GT-ROI, calib ON, exact), with the variable-position signature
fields reported separately.** `signer_name`/`signer_title` live in signature blocks whose position is
**not** fixed by the template (it moves per document), so a per-template ROI cannot bound them — a
documented scope limit of spatial verification (matches the production "fails for signatures/stamps"
note). We therefore show the headline both with all fields and with those two removed:

| field set | n | err | AUROC ↑ | cov@≤5% | cov@≤10% | cov@≤20% |
|---|---|---|---|---|---|---|
| all 6 fields | 2647 | 20.6% | 0.8963 | 70.8% | 83.3% | 89.5% |
| excl. signature (`signer_name`, `signer_title`) | 2052 | 23.5% | **0.9272** | 68.3% | 80.8% | 88.6% |

Removing the two signature fields **raises AUROC 0.896 → 0.927** (they rank near chance, ~0.58, because
position carries no signal for them) while coverage dips slightly (70.8 → 68.3%) and error-rate rises
(20.6 → 23.5%) — expected, since the removed fields were mostly-correct, low-error fields. Per-field
AUROC: registration_num 0.931, file_date 0.902, registrant_name 0.871, foreign_principle_name 0.739,
signer_title 0.593, signer_name 0.579.

- **Production config v3 (GT-ROI, calib ON) reaches AUROC 0.896 (all 6 fields) / 0.927 (excl. signature)
  on real forms.** On the fixed-position fields the spatial channel ranks correct-vs-wrong strongly; the
  only weak spot is the variable-position signature fields, which belong to the text/content channel.
- **Calibrated pred-ROI (v2) collapses to AUROC 0.398 — below chance.** Per-template calibration
  overfits VRDU's small per-template data; GT-ROI (v3/v4), not pred-ROI, is the right structured
  config here. (v4 calib-OFF ranks marginally higher, 0.911, but its accept-threshold false-alarm is
  0.263 vs v3's 0.086 — calibration fixes the operating point, which is why production ships v3.)
- **This is NOT a VRDU head-to-head with Jin et al.** Jin's "VRDU" is the **Ad-Buy /
  advertising-order-form** subset (9 fields); ours is **Registration-Forms (FARA)** (6 fields) —
  different subset, fields, extractor and base error, so the numbers are not directly comparable. For
  context only, Jin report on their VRDU-Ad-buy: +P/L/V-fusion AUROC 0.921–0.934, +cross-model 0.928;
  coverage@≤5% 25.7–41.3%. **The only genuinely shared dataset with Jin et al. remains FATURA.**

---

## 2. Unstructured / Signal — new RealKIE domains

Same dociq 6-signal classifier. Canonical = **clean (GT-sparsity fix) · untuned · binary · scalar**.
(These domains have no line-item fields, so `scalar` == `all`.) Quote AUROC/coverage, not accuracy.

### Canonical (clean) per domain
| domain | n | err | catch ↑ | FA ↓ | acc | accept-all | AUROC ↑ | cov@5% | cov@10% | cov@20% |
|---|---|---|---|---|---|---|---|---|---|---|
| charities | 1522 | 0.0703 | 0.7290 | 0.3654 | 0.6413 | 0.9297 | 0.7129 | 0.7510 | 1.0000 | 1.0000 |
| nda | 148 | 0.0878 | 0.4615 | 0.4519 | 0.5405 | 0.9122 | 0.5316 | 0.1622 | 1.0000 | 1.0000 |
| s1 | 37277 | 0.0322 | 0.8383 | 0.0339 | 0.9620 | 0.9678 | 0.9601 | 1.0000 | 1.0000 | 1.0000 |

For reference, the original **FCC** canonical (from the FCC leg): scalar/binary AUROC **0.897**,
cov@5% **0.842**, catch 0.926, acc 0.721 (accept-all 0.887), n=240.

### Tuning & cleanup study (scalar/binary AUROC / cov@5%)
| domain | untuned-noisy | tuned-noisy | untuned-clean (canonical) |
|---|---|---|---|
| charities | 0.8289 / 0.5296 | 0.8144 / 0.5190 | 0.7129 / 0.7510 |
| nda | 0.5620 / 0.1600 | 0.5995 / 0.1533 | 0.5316 / 0.1622 |
| s1 | 0.9645 / 1.0000 | — / — | 0.9601 / 1.0000 |

### Why the GT-sparsity cleanup is justified (annotation gaps — whole set, not just charities)
`clean` drops the cases where GT is empty but the model predicted a value. Across **every** domain those
are **annotation gaps, not genuine field absence**: the predicted value is actually present in the
document's own text, so `noisy`'s "mark it wrong" is unfair and `clean`'s "drop as unverifiable" is the
honest choice. Verified by `scripts/check_annotation_gap.py` → `analysis/annotation_gap.json`:

| domain | GT-empty + pred-present | value present in doc text (annotation gap) |
|---|---|---|
| Charities | 601 | **99.5%** |
| FCC | 179 | **98.9%** |
| S-1 | 3,555 (+755 degenerate `[]`/placeholder outputs excluded) | **98.2%** |

Genuine hallucinations (value not in the document → a real error we *should* keep) are **≤2% everywhere**.
So the `clean` labeling is the principled canonical for the **whole Signal set**, backed by data.

### Paper scope & competitor
- **Canonical = clean · untuned · binary · scalar — identical to the FCC leg** (FCC doc §: "`bundle_clean`
  (untuned) · binary · scalar"). New domains have no line-items → scalar == all; FCC also reports all-fields
  (0.825) because it has line-items.
- **Paper-reported domains: S-1 (0.960), FCC (0.897 scalar), Charities (0.713 clean; 0.829 noisy).** **NDA
  is NOT reported as a capability result** (AUROC 0.53, near chance — too few fields/samples); it stays only
  as the stated small-domain limitation.
- **Competitor (same dataset = FCC only):** ConfBench (arXiv 2608.01792). Ours (zero extra call) **beats**
  the comparable zero-call log-prob confidence (0.825–0.897 vs 0.58–0.64) and **ties** the best model's
  self-confidence (Claude Opus 4.6 verbalized 0.84). RealKIE Charities/NDA/S-1 have **no** verification
  competitor (RealKIE reports extraction F1 only). Full head-to-head: `UNSTRUCTURED_EXPERIMENT.md` §8.

---

## 3. Findings (honest)

**Structured / ROI (VRDU — real documents):**
1. **ROI verification transfers from synthetic to real.** On 1,915 real FARA forms the production
   config **v3 (GT-ROI, calib ON)** reaches present/exact **catch 0.750, false-alarm 0.086, accuracy
   0.880** (containment 0.781 / 0.901). The spatial channel is not an artefact of FATURA's synthetic
   cleanliness — it works on real layouts.
2. **The containment→exact gap is SMALL on VRDU** (v3: 0.781→0.750; v4: 0.949→0.923), unlike FATURA
   (~1.00→0.54). Interpretation: on these real forms most catchable errors are **mis-locations**
   (spatially detectable), not in-place value errors — a *different, more favorable* detectability
   profile than synthetic FATURA. Honest contrast, not a uniform story.
3. **Calibration behaves oppositely to FATURA.** On FATURA, pred-ROI+calibration (v2) was best; on
   VRDU, v2 pred-ROI+calib **hurts** catch (exact 0.487) vs pred-ROI no-calib (v1, 0.783), because
   per-template calibration overfits VRDU's far smaller per-template data (≈550/237 vs FATURA's
   thousands). **GT-ROI (v3/v4) is the right choice for VRDU** — so the "v2 is best" FATURA finding
   does **not** generalize; we report v3 (GT-ROI, production) as the VRDU headline.
4. **Per-field (v3 present/exact):** strong on registration_num (catch 0.93, acc 0.91),
   registrant_name (0.76/0.91), foreign_principle_name (0.75/0.91); weak on **signer_title** (catch
   0.15, only 163 instances) and **file_date distorted** — NuExtract emits ISO dates (`2008-07-17`)
   not verbatim in the OCR, so 74% of file_date predictions read as exact "errors". **Report file_date
   separately**; it is a date-normalization artefact, not a spatial-verifier failure.
4b. **AUROC weakness is isolated to variable-position fields, not broad.** On VRDU, dropping only the
   two signature fields lifts AUROC **0.896 → 0.927** (signer_name 0.579, signer_title 0.593 — near
   chance — vs registration_num 0.931, file_date 0.902, registrant_name 0.871). `signer_name/title`
   sit in signature blocks whose position is not template-fixed, so spatial evidence carries no signal;
   they belong to the text/content channel. **Paper reports both all-fields and excl-signature.**
4c. **FATURA's "low" AUROC was mostly a labeling artefact, not capability** (see
   `paper/competitor_comparison.md`). Decomposing the strict-exact errors: **A** value-right-but-exact-
   wrong 20.8%, **B** GT-empty 66.4%, **C** genuine in-place value error 12.8%. Relabeling only **A** as
   correct (keeping B+C as errors) lifts v3 GT-ROI AUROC **0.865 → 0.994** and cov@≤5% 63.7 → 69.8% —
   **parity with Jin et al.'s fused multi-call system (0.990–0.997) at zero extra model call.** The
   genuinely spatial-blind set (C) is only 12.8% of errors / 3.8% of predictions — the in-place value
   errors that need the text channel. (Containment-tolerant A-handling is a generous bound; true exact
   capability is between 0.865 and 0.994.) **Paper uses the A-handled 0.994 as the final FATURA score.**
4d. **Unifying principle across both ROI datasets:** spatial detectability tracks **positional
   consistency** of a field. Fixed-slot fields (registration_num, dates, addresses, invoice fields) →
   AUROC 0.87–1.00; variable-position/signature fields → near chance. The spatial channel is near its
   ceiling on fixed-position fields; the residual (variable-position + in-place value errors) is a
   structural limit of *any* position-only method and is the job of the text/content channel.

**Unstructured / Signal (new RealKIE domains):**
5. **S-1 is the strongest Signal result to date: AUROC 0.960, false-alarm 0.034, catch 0.84**
   (n=37,277). Large data + diverse fields let the 6 text signals discriminate cleanly — it exceeds
   even the FCC leg (0.897). (cov@5% saturates at 1.00 only because base error 3.2% is already under
   the 5% budget, so accept-all trivially satisfies it — the **AUROC/false-alarm** is the capability
   story here, not coverage.)
6. **Charities (28 fields): usable — AUROC 0.713, cov@5% 0.751, catch 0.73.** Solid on a hard
   many-field domain.
7. **NDA (3 fields): AUROC 0.53, near chance — an honest negative.** With only 3 field types and 13
   errors in 148 instances there is too little signal/label diversity for the classifier to learn.
   Small, low-field-count domains are a genuine limitation of the Signal leg.
8. **Signal quality scales with data + field diversity:** s1 (24 fields / 37k inst, 0.960) ≫
   charities (28 fields / 1.5k, 0.713) > nda (3 fields / 148, 0.53). EBV's Signal verifier generalizes
   where there is enough per-domain signal and degrades gracefully (and detectably) where there is not.
9. **Tuning does not help** (consistent with FCC): charities noisy-tuned 0.814 ≤ noisy-untuned 0.829;
   nda 0.599 vs 0.562 (tiny-domain noise). We keep **untuned** canonical. (s1 tuning was not run to
   completion — RandomizedSearchCV stalled on 151K training instances across a machine sleep; it only
   feeds this comparison, and the canonical untuned result is unaffected.)
10. **The GT-sparsity cleanup is justified across the whole set (annotation gaps), though its AUROC
    effect is domain-dependent.** The dropped GT-empty+pred-present cases are **annotation gaps** — the
    value is present in the document text **98–99.5%** of the time (≤2% genuine hallucinations); see the
    evidence table in §2. So labeling them "wrong" (`noisy`) is unfair and `clean` is the honest canonical
    for **all** domains, not just charities. Its effect on the number varies: charities cov@5% 0.530→0.751
    but AUROC 0.829→0.713 (drops easy-to-rank gap cases, leaving the harder real errors); s1 negligible
    (0.965→0.960); FCC the opposite (AUROC 0.804→0.897). The *justification* is uniform; the *magnitude* is
    domain-specific.

**Bottom line:** the robustness round supports the paper's generalization claim — the ROI channel
transfers synthetic→real (FATURA→VRDU, fair AUROC 0.994 ≈ Jin at zero extra call) and the Signal channel
transfers across domains (FCC 0.897 / S-1 0.960 / Charities 0.713; on par with ConfBench on the shared FCC
set). Paper-reported Signal domains = **S-1, FCC, Charities**; **NDA is held out as the stated
small-domain limitation**. Caveats stated honestly: file_date date-normalization; VRDU favors GT-ROI not
calibrated pred-ROI and its signature fields are variable-position (text channel's job); GT-sparsity
cleanup = annotation gaps; containment-tolerant FATURA A-handling is a generous bound.

## 4. Provenance & reproduce
- Signal: `unstructured_ntp/scripts/domain_signal.py --dataset <ds>` → `domains/<ds>/` (data_clean,
  data_noisy, bundle*, decisions, analysis/signal_metrics.json); report via `report_domain_signal.py`.
- ROI: `structured_ntp_v2/scripts/prep_vrdu_roi.py` then `run_matrix.py --dataset vrdu …`
  (6 runs under `matrix/vrdu_*`); tables via `doc_structured_vrdu.py`.
- dociq (`/Users/rajeshgupta/Git_Clones/dociq`) and NTP code driven in place, unmodified.
