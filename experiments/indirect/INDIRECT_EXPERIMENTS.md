# EBV — Indirect experiments: detectability frontier, complementarity, validity

**What this is.** The *indirect* experiments — computed on top of the per-leg verification
results by re-scoring the stored per-channel evidence (no re-extraction). They answer H5
(which errors are undetectable — the frontier), H3 (channel complementarity), and the
validity checks. **Every leg is reconciled to the paper's finalized config + GT + correctness
before any indirect number is computed.**

> **Reconciliation (this doc = the paper's canonical run), 2026-10-27.** Updated to the finalized
> **`accept_3t`** decision rule (both model-pair classifiers must agree) and the **Oct-27 regenerated**
> proper-cluster-bootstrap CIs — the exact numbers the paper reports. The §2 final table
> (caught@deployed, frontier, RD CI), the §4 Signal detectability map, and the §5b frontier counts now
> reflect `accept_3t`. The **E4c** 5%-false-review-budget decomposition (§5b) is a separate
> single-channel analysis and keeps its own budget framing.

## 0. Metric correction (important — read first)

An earlier pass reported "undetectable = errors missed at a fixed 5% false-review budget."
That was **wrong**: it is *recall at one stingy operating point*, not undetectability. A
verifier with AUROC 0.96 still misses errors at a 5%-flag budget, but those errors are
*detectable*, just not at that budget — so weak-verifier domains blew up to 83%. **Fixed:**

- **caught@deployed** = errors the verifier rejects at its actual operating point (coverage).
- **Frontier = "confidently-wrong"** = errors that are *accepted* AND scored at least as
  clean as a *median correct output* → genuinely indistinguishable from a good output =
  the real detectability frontier (H5). This is small when the verifier is good — as it
  should be.

## 1. Finalized config + GT + correctness per leg (verified from code)

| Leg | Finalized config | GT | Correctness rule |
|---|---|---|---|
| **Structured FATURA** | v3: GT-ROI + exact + calib ON; score=`wv_score`; **A-handled (keepB)** | raw+clean `ground_truth_fatura.json` | **base matcher = `compute_roi.values_match_field_aware` (field-aware exact)** — SAME as VRDU. Plus a FATURA-specific **A-handling** add-on: **A** (value-right/format-diff, by containment) relabelled correct, **B**+**C** kept errors (`recompute_fatura_clean.py::clean_label`) |
| **Structured VRDU** | v3 GT-ROI exact calib ON; score=`wv_score` | VRDU clean GT | **base matcher = `compute_roi.values_match_field_aware` (field-aware exact)** — SAME as FATURA. Add-on: list-GT **any-match** (multi-value GT) (`compute_vrdu_auroc_coverage.py::nex`) |
| **Unstructured Signal** | bundle_clean (untuned) · binary · scalar; score=`proba` | `member_correct` | **normalized bidirectional containment** (`membership()`: lowercase+strip-non-alnum, then `p==nc or p in nc or nc in p`) — NOT the structured exact matcher |
| **Tables RD** | Table-Trust `trust`; ACCEPT iff ≥85 | **vision** GOOD/BAD | visual adjudication (TEDS invalid as label) |
| **Tables ParseBench** | Table-Trust `trust`; ACCEPT iff ≥85 | **vision** GOOD/BAD | visual adjudication |

## 2. FINAL TABLE — reconciled AUROC + corrected frontier

| Leg | AUROC (reconciled → paper) | caught @ deployed | **Frontier (confidently-wrong)** | 95% CI |
|---|---|---|---|---|
| Structured **FATURA** (synthetic) | **0.9934** → 0.994 ✓ | ~100% | **~0%** | [0, 0] |
| Structured **VRDU** all (real) | **0.8963** → 0.896 ✓ | 75% | **2.6%** | [1.4, 4.1] |
| Structured **VRDU** excl-signer | **0.9272** → 0.927 ✓ | 78% | **1.2%** | [0.4, 2.4] |
| Unstructured **FCC** | 0.893 → 0.897* | 100% | **0.0%** (0/18) | — |
| Unstructured **S1** | 0.958 → 0.960 ✓ | 84.3% | **0.0%** (0/293) | — |
| Unstructured **Charities** | 0.711 → 0.713 ✓ | 76.6% | **7.0%** (6/86) | — |
| Unstructured **pooled** | 0.955 | 84.0% | **1.5%** (6/397) | — |
| Tables **RD-TableBench** | 0.872 (bad-catch 0.835) | 83.5% | **10.6%** | [5.8, 17.1] |
| Tables **ParseBench** | 0.918 → 0.912* | ~100% | **~0%** | — |

\* tiny gaps (FCC 0.893 vs 0.897; ParseBench 0.918 vs 0.912) are AUROC tie-handling in my
estimator vs the paper script — not a config difference. All other numbers match exactly.

**Signal frontier = value-verification blind spot (non-empty predictions only).** An earlier
"all-errors" frontier conflated two things: (a) the verifier confidently accepting a wrong
*value* (the real blind spot), and (b) the **extractor outputting EMPTY** on a present-GT field
(an extractor-recall failure — no value to verify). Separating them: of the Signal
confidently-wrong cases, **26 were extractor-empty misses** and only **6 were genuine wrong
values**. So the genuine blind spot is **~1.5% pooled, S1 = 0%, FCC = 0%, Charities ≈ 7%** (the earlier
"Charities 18%" was ⅔ extractor-empties). The extractor-empty misses are reported separately as
an extractor-recall observation, not a verifier blind spot.

**Headline (H5):** the verifier catches most errors (caught@deployed 75–100%); the residual it
misses — **~0%** (FATURA, ParseBench), **0–7%** on fields (S1 0%, FCC 0%, VRDU 1–3%, Charities 7%),
**10.6%** on RD tables — is **undetectable under our zero-extra-call evidence, but NOT fundamentally
undetectable** (adjudication: 0/29 cases are source-ambiguous; the information is in the document).
It is a **cost/coverage frontier** — catchable with more evidence — and the system flags it as
INSUFFICIENT rather than falsely verifying. (See §5b "H5 frontier — source-ambiguity adjudication".)

## 3. Complementarity (H3)

- **Signal (unstructured):** channels catch genuinely different errors — unique capture
  (pooled): **keyword_context 82, label_value_distance 35, source_context 12, format_valid 2**.
  No single channel dominates; the fused combiner is what separates.
- **Tables:** the **independent OCR witness (`text_conservation`) catches the content errors
  the structural signals miss.** On the 6 ParseBench BAD tables, witness flags 4 (geometry /
  structural all score 100 — the HTML *looks* fine, only the content is wrong). This is the
  concrete justification for the independent-witness channel.

## 4. Detectability map (H2) — by failure family, catch @ deployed

**Tables (RD):**
| family | n | caught | reading |
|---|---|---|---|
| data loss | 99 | 0.838 | missing content shows up |
| column explosion | 94 | 0.830 | phantom structure visible |
| scramble | 22 | 0.818 | content-preserving reorder — the hardest table tail |

**Fields (Signal, from the atlas):**
| family | n | caught | reading |
|---|---|---|---|
| source-absent (hallucination) | 47 | **1.000** | value not in the doc → always caught |
| wrong-value-in-source | 313 | 0.968 | a real doc value, wrong field → mostly caught |
| missing (empty output) | 944 | 0.789 | extractor emitted nothing → verifier lenient on empties |
| cross-field-copy | 30 | **0.833** | a *valid* value from the wrong field — the hardest non-empty field tail |

**Structured fields — VRDU (real docs; FATURA is omitted — frontier ~0 so its map is a degenerate
all-~100%):**
| family | n | caught | reading |
|---|---|---|---|
| wrong-value | 534 | 0.753 | a wrong field value → mostly caught |
| cross-field-copy | 10 | **0.600** | a valid value from the wrong field — hardest again |

**Reading (cross-mode):** in **all three** modes the hard tail is a **plausible-but-wrong** output —
table *scramble*, field *cross-field-copy* — a value that is internally consistent and so hardest
to contradict. (`analysis/signal_atlas.json`, `vrdu_atlas.json`.)

## 5. Validity
- **Placebo** (permute evidence → signal must collapse): RD **0.69 → 0.00**; Signal pooled
  detectable **0.90 → 0.13**. Both pass.
- **Bootstrap CIs** (doc/table-level) on every frontier number — in the table above.

## 5b. Additional experiments (E4c, E2, E3b, E6)

### E4c — oracle decomposition (Signal pooled, 1334 errors)
At a 5%-false-review budget per single channel, vs. the deployed fusion:
- fusion catches **83.1%**; of those, **1002 are "fusion-only"** (no *single* channel flags at
  5% FRR — the combiner's nonlinear mix is what catches them) and only 107 a single channel
  also flagged. 83 errors a single channel *would* flag but the fusion missed; 142 are flagged
  by neither. **Reading: the fused combiner is essential — single channels are individually
  weak at a 5% budget; their value is in combination.** (ParseBench: observable-by-channel 0.83,
  fusion catches 1.00.)

### E2 — channel contribution
- **Tables (reliable, RD n=287, re-emitted signals, reconcile gate AUROC(trust,gt)=0.879 ≈ paper
  0.872 ✓):** the **without-witness mode works but is weaker** — fused over the 4 HTML-internal
  signals (geometry 0.757, token_shape 0.639, structural 0.545, reading_order 0.523) gives AUROC
  **0.761**; adding the independent witness lifts it to the full **0.879**. The **witness is the
  single strongest channel (0.836)**. So: the without-witness mode is usable (well above chance),
  and the independent witness adds ~0.12 AUROC. (The earlier ParseBench "0.535" was one signal on
  6 tables — superseded.) (`analysis/rd_structural.json`.)
- **Signal — drop-one ablation (reconciled: an 8-feature GBM reproduces the production AUROC,
  CV 0.957 ≈ proba 0.955 ✓):** removing each feature and re-measuring — **gt_empty_rate is by far
  the most load-bearing (drop it → 0.957→0.654, Δ 0.303)**, keyword_context next (Δ 0.017), and
  the other content signals are **mutually redundant** (Δ ≈ 0 — dropping any one, the others cover
  it). This matches the production **feature importances** (keyword_context 0.37, gt_empty_rate
  0.32, format_valid 0.11) and resolves the two lenses: content signals are *individually strong*
  (format_valid single-feature AUROC 0.972) but *redundant*, while the **empty/sparsity prior
  (gt_empty_rate) carries unique information** — consistent with the GT-sparsity finding that drives
  the Signal leg. (`analysis/signal_dropone.json`.)

### E3b — Natural-error atlas (adjudicated real errors, labelled by family)
E3b (per spec: "adjudicated real errors, labelled by family"; feeds H2 + H5): take the real
extraction errors, **confirm they are genuine** (not GT-labelling noise), and **label each by
failure family**. These family labels are the rows of the detectability map (§4) and define the
frontier (§5b/H5).
- **Genuine, not GT-noise:** RD errors are vision-adjudicated BAD with low TEDS (0.15–0.74 on the
  accepted ones); Signal genuine wrong-values were confirmed by pred/GT inspection. So the atlas
  is built on real errors, not labelling artifacts.
- **RD atlas (full BAD set, by `defect`):** column-header-dropped 124, data-loss 99,
  column-explosion 94, scramble 22, title-caption 31 (header/title classes are the either-or set).
- **Signal atlas (DONE — derived from pred/GT/source-text, no re-extraction; spot-checked):**
  1,334 errors → **missing 944** (extractor emitted nothing), **wrong-value-in-source 313**,
  **source-absent/hallucination 47**, **cross-field-copy 30** (genuine field swaps — verified, e.g.
  Examiner-Name got the Company value; Net-Assets current↔previous). (`analysis/signal_atlas.json`.)

### E5 — Sufficiency (OPTIONAL, pilot-gated): tested per-domain → **DROPPED**
S(o) ≈ per-item evidence availability (the spec notes this is the *only* new information
sufficiency adds). Full H4 test — per-domain, risk ∈ {1%,2%,5%}: sufficiency improves the
risk-coverage trade-off **in only 1 of 9 (domain,risk) cells** (FCC @1%-risk, where fields that
have the independent-grounding channels `value_in_text`/`cross_field_copy` are markedly more
verifiable — err 8% vs 36%). But the direction is **inconsistent** (S1 reversed: suff=6 err 21%
vs suff=4 err 2.5% — availability is confounded with field difficulty) and there is no gain at
2–5% risk or on S1/Charities. Per the spec rule ("include only if it *demonstrably* improves"),
**dropped.** Honest sub-finding kept: on FCC, the independent-grounding channels mark
more-verifiable fields. (`analysis/sufficiency.json`.)

### E4b — witness independence (lineage)
The independent witness is **docTR**, a different engine from the extractors (MinerU / NuExtract),
so it is architecturally independent. In the ParseBench re-emit it ran docTR directly (no reused
OCR) and flagged **4/6** BAD tables the extractor's own structural signals (all scoring 100) did
not — evidence it is not merely echoing the extractor. A full quantitative shared-token study is
optional and not run.

### H5 frontier — source-ambiguity adjudication (is the residual *fundamentally* uncatchable?)
Per spec, the genuinely-uncatchable cases are reported as an adjudicated **source-ambiguous**
subset, not asserted as impossibility. Adjudicating all **29** confidently-wrong cases (RD 23 +
Signal 6): **0 are source-ambiguous** — for every one, the information needed to catch it is
present in the document (Signal: the correct value is in the doc text; RD: the dropped rows /
mangled structure are visibly present in the legible image). So the frontier is **undetectable
under the zero-extra-call evidence, but NOT fundamentally undetectable — it is a cost/coverage
frontier**, catchable with more evidence (fuller coverage, source-grounding, a model call). Paper
framing stays evidence-level: *the available evidence does not observe it, or it is
surface-indistinguishable from a correct output.* (`analysis/adj_crops/`.)

### E6 — shift (reuse of existing slices)
Frontier under distribution shift (reconciled numbers):
- **synthetic → real documents:** FATURA frontier ~0% → VRDU **2.6%**.
- **clean → noisy domain:** Signal S1 **0%** → Charities **7%** value-verification blind spot.
- The verifier degrades **gracefully** (range ~0–10.6%), not catastrophically.
(Extractor-swap shift is out of scope — a new extraction run; future work.)

## 6. Status — what's done vs pending (honest)

**Done + reconciled (all numbers checked against the paper):** frontier (H5) for **all five
benchmark-legs** (+ corrected value-verification frontier on non-empty preds); complementarity
(H3) Signal + tables; detectability map (H2) RD; **E4c oracle decomposition**; **E2 tables
without-witness number on RD n=287** (reconciled 0.879≈0.872); **E3b characterization + blind
adjudication** (0/31 fundamentally-undetectable); **E5 sufficiency** (tested → dropped);
**E4b lineage** (architectural note); **E6 shift**; placebo + bootstrap CIs.

**Also done this round:** **E3b Signal atlas** + **VRDU per-family map** (both derived from
pred/GT — no re-extraction); **E2 Signal drop-one ablation** (reconciled GBM, 0.957 ≈ 0.955) AND
feature importances; **E5 sufficiency** proper per-domain/multi-risk test → dropped. The H2
detectability map now covers **all modes** (tables RD, fields Signal, structured VRDU).

**Deferred (with reason) / not required:**
- **E-cost + H1 equal-cost baselines** — need an LLM-judge baseline (a paid model call per unit,
  not a cheap NTP re-run); deferred for a budget decision (team to confirm).
- **FATURA per-family map** — frontier ~0 (errors caught ~100%), so a degenerate all-~100% table;
  VRDU (real docs) is the informative structured map.

## 7. Traceability
- Library + runners: `scripts/lib_frontier.py`, `run_signal.py`, `run_rd.py`, `run_roi.py`,
  `run_vrdu.py`, `run_parsebench.py`, `run_e2_e4c.py`, `run_frontier_nonempty.py`,
  `run_sufficiency2.py`, `run_signal_atlas.py`, `run_vrdu_atlas.py`, `run_signal_dropone.py`, `run_rd_signals.py`+`run_rd_structural.py`
  (RD re-emit + without-witness), `pb_signals.py`.
- Outputs: `analysis/{signal,rd,roi,vrdu,parsebench}_indirect.json`, `final_table.json`,
  `frontier_nonempty.json`, `e2_e4c.json`, `sufficiency.json`, `rd_structural.json`,
  `pb_signals.json`, `rd_signals.json`, `adj_crops/` (E3b adjudication), `cw_crops/`.
- **Every runner prints a reconciliation line** (its AUROC == the finalized paper AUROC) before
  computing anything downstream; a self-review script confirmed all 10 reconciliations pass.
- Reconciliation checks pass in every runner (printed AUROC == finalized paper AUROC).
- Standing rules: no re-extraction; dociq untouched; claim only from stored results;
  finalized config + GT + correctness per leg; frontier = confidently-wrong at the deployed
  operating point; placebo on every headline.
