#!/usr/bin/env python3
"""Generate UNSTRUCTURED_EXPERIMENT.md from the computed metrics (no hand-typed numbers)."""
import json
from pathlib import Path
EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
UNS = EBV / "experiments" / "unstructured_ntp"
M = json.loads((UNS / "realkie_fcc" / "analysis" / "signal_metrics.json").read_text())
S = json.loads((UNS / "realkie_fcc" / "data" / "split.json").read_text())


def row(tag, m):
    g = lambda k: "—" if m.get(k) is None else m[k]
    return (f"| {tag} | {m['n']} | {m['err_rate']} | {g('error_catch')} | {g('false_alarm')} | "
            f"{g('route_prec')} | {g('accuracy')} | {g('AUROC')} | {g('cov@5%')} |")


hdr = ("| population / mode | n | err-rate | error-catch ↑ | false-alarm ↓ | route-prec ↑ | accuracy ↑ | AUROC ↑ | cov@≤5% ↑ |\n"
       "|---|---|---|---|---|---|---|---|---|")
tbl = "\n".join([hdr,
                 row("scalar / binary", M["scalar"]["binary"]),
                 row("scalar / 3tier", M["scalar"]["3tier"]),
                 row("all / binary", M["all"]["binary"]),
                 row("all / 3tier", M["all"]["3tier"])])
suf = M["sufficiency"]
psig = M["per_signal_mean"]
sig_tbl = "\n".join(["| signal | mean(correct) | mean(wrong) |", "|---|---|---|"] +
                    [f"| {k} | {v['mean_correct']} | {v['mean_wrong']} |" for k, v in psig.items()])

doc = f"""# Signal (unstructured) NTP experiment — full documentation

Verifies unstructured-field extraction values with dociq's **production Signal classifier**
(6 text signals → tabular model → accept/route), with **no extra LLM/VLM call**, on
**RealKIE-FCC** invoices. Extractor = NuExtract-3. Run fully **offline**, driving dociq's
own code in place; **dociq repo untouched**, paper-local venv at `unstructured_ntp/.venv`.

## How it ran (and why training was ~2 min)
- `score_new_data.py` computes the 6 signals; `run_ntp_direct_classifier.py` auto-labels
  correct/wrong from ground truth (field-aware matcher) and trains the classifiers.
- **Models trained: 2** — RandomForest(500) + GradientBoosting(300), for the single doc-type
  `invoice`. Binary mode uses the best single (gbm); 3-tier uses both as the agreement pair.
- ~2 min because the training table is small (~1,540 field-rows × 9 features) and we passed
  `--skip-tuning` (no RandomizedSearchCV). Models are real sklearn objects on disk in `bundle/models/`.

## Data / split
- {S['n_docs']} FCC docs ({S['skipped']} skipped = failed extractions), **{S['n_train']} train / {S['n_test']} test** (80/20, seed {S['seed']}).
- Inputs per doc: `{{field:value}}` (NuExtract), full document text, doc_type `invoice`. **No OCR/positions** — the 6 signals recompute positions internally from text.

## Methodology
- **Correctness = membership**: a prediction is correct if it matches ANY ground-truth value of
  the field (FCC has multi-value "Line Item - *" fields; NuExtract emits one value). Reduces to
  normal single-value match for scalar fields.
- **Scalar vs line-item split**: the 6 scalar fields (Agency, Advertiser, Gross Total, Net Amount
  Due, Agency Commission, Payment Terms) are the clean single-value KIE targets; the 5 "Line Item"
  fields are tabular (belong to the table leg) — reported separately.
- **Binary** (accept=NTP / route=REVIEW) is primary; **3-tier** collapses {{LLM_REVIEW, HUMAN_REVIEW}}→route.
- Continuous score for AUROC/coverage = the best model's **predict_proba** (hard-label decision has
  no native probability; we build features in the model's own `feature_names_in_` order).

## Results (held-out test; score = best-model predict_proba)
{tbl}

Sufficiency / empty handling: `empty_prior_applied`={suf['empty_prior_applied']}, `gated`={suf['gated']},
3-tier routing = {suf['tier3_breakdown']}.

### Per-signal separation (mean value: correct vs wrong fields)
{sig_tbl}

## Findings (honest)
1. **Scalar fields are the real result:** AUROC **{M['scalar']['binary']['AUROC']}**, auto-approve **{round(M['scalar']['binary']['cov@5%']*100,1)}% at ≤5% error**.
2. **Line-item fields drag it down** (all-fields AUROC {M['all']['binary']['AUROC']}, cov@5% {round(M['all']['binary']['cov@5%']*100,1)}%) — confirming they are tabular, not single-value Signal targets.
3. **At the production default threshold the model over-routes** (false-alarm ~{M['scalar']['binary']['false_alarm']}, accuracy {M['scalar']['binary']['accuracy']} — below accept-all). The proba still discriminates (AUROC {M['scalar']['binary']['AUROC']}), so the **risk-coverage curve**, not the default threshold, is the capability story.
4. **Harder end of the detectability frontier:** Signal on messy real FCC invoices is weaker than ROI on clean FATURA — the expected, honest contrast.
5. **Caveat:** small test ({M['scalar']['binary']['n']} scalar instances) → sampling noise.

## Directory map (experiments/unstructured_ntp/)
```
.venv/                     paper-local venv (sklearn, joblib, pandas) — dociq untouched
scripts/                   build_fcc_dataset, train_signal, infer_signal, analyze_signal, doc_unstructured
data/{{train,test}}/invoice.json   dociq-format records ; data/meta/*  raw gt+pred+field_type ; data/split.json
scored/ , scored_test/     score_new_data signal output (train / test)
bundle/                    trained models + configs + empty-prior + dociq CSVs (field/doc-level, predictions,
                           three_tier_routing, feature_importance, DIRECT_NTP_RESULTS.md, ntp_metrics_summary.xlsx)
decisions/fcc_decisions.jsonl   per-field: decision(binary+3tier), proba, final_score, 6 signals, empty-prior
analysis/signal_metrics.json    the metrics above
logs/                      build / train / infer / analyze logs (full training output incl. internal CV)
paper/signal_results.md , paper/UNSTRUCTURED_EXPERIMENT.md
```

## Reproduce
```
PY=experiments/unstructured_ntp/.venv/bin/python
$PY scripts/build_fcc_dataset.py
$PY scripts/train_signal.py     # drives dociq score_new_data + run_ntp_direct_classifier (cwd=dociq)
$PY scripts/infer_signal.py     # engine predict_document (binary+3tier) + best-model predict_proba
$PY scripts/analyze_signal.py
$PY scripts/doc_unstructured.py
```

## Data provenance
Predictions+GT: `experiments/results/realkie_fcc_results/`. Text: `realkie_fcc_invoices/train.csv`.
Signal code: `/Users/rajeshgupta/Git_Clones/dociq/app/ntp_classifier/` (run in place, unmodified).
"""
(UNS / "paper").mkdir(exist_ok=True)
(UNS / "paper" / "UNSTRUCTURED_EXPERIMENT.md").write_text(doc)
print("wrote", UNS / "paper" / "UNSTRUCTURED_EXPERIMENT.md")
print("\n" + tbl)
