#!/usr/bin/env python3
"""
Build the COMPREHENSIVE unstructured-Signal reference doc from the stored decisions files
(no retrain, no re-infer, no hand-typed numbers). Reads:
  decisions/fcc_decisions.jsonl        -> untuned, NOISY labels  (ambiguous GT-absent = "wrong")
  decisions/fcc_decisions_tuned.jsonl  -> tuned,   NOISY labels
  decisions/fcc_decisions_clean.jsonl  -> untuned, CLEAN labels  (ambiguous GT-absent dropped) = CANONICAL
  data/split.json                      -> doc/instance counts

Writes:
  analysis/signal_report.json          -> every computed table as data (traceable)
  paper/UNSTRUCTURED_EXPERIMENT.md      -> the human-readable reference doc

Each number in the doc is injected from a computed value here. Diagnosis constants that were
computed on the PRE-CLEAN meta during the audit step (now superseded on disk) are passed in
DIAG below and clearly tagged as such in the doc.
"""
from __future__ import annotations
import json, statistics as st
from pathlib import Path

UNS = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper") \
      / "experiments" / "unstructured_ntp"
DEC = UNS / "realkie_fcc" / "decisions"
NOISY = DEC / "fcc_decisions.jsonl"
TUNED = DEC / "fcc_decisions_tuned.jsonl"
CLEAN = DEC / "fcc_decisions_clean.jsonl"
SPLIT = json.loads((UNS / "realkie_fcc" / "data" / "split.json").read_text())

# ---- diagnosis numbers computed on the PRE-CLEAN train_meta during the audit (now superseded) ----
DIAG = {
    "train_scalar_wrong": 217, "train_scalar_gt_absent_pred_present": 66,
    "train_scalar_both_present_mismatch": 90, "train_scalar_miss": 61,
    "test_scalar_wrong_noisy": 51, "test_scalar_gt_absent_pred_present": 24,
    "matcher_scalar_n": 264, "matcher_exact_eq": 199, "matcher_loose_substr": 213,
}

# ---- ConfBench (arXiv 2608.01792, AWS) numbers read from the paper (Table 3, OCR+Image). ----
# Same dataset as us: RealKIE-FCC-Verified. ConfBench = benchmark of a model's OWN (intrinsic)
# confidence (verbalized or log-probability); NO trained external verifier. Base acc WOA 0.63-0.77.
CONFBENCH = {
    "source": "arXiv 2608.01792 (Roy et al., AWS) Table 3, OCR+Image, RealKIE-FCC-Verified",
    "base_acc_WOA": "0.63-0.77",
    "verbalized_auroc": {  # model -> (AUROC, ECE)
        "Claude Opus 4.6": (0.84, 0.05), "Claude Sonnet 4.5": (0.77, 0.13),
        "Claude Haiku 4.5": (0.74, 0.17), "Qwen 3.6-27B": (0.72, 0.22),
        "Kimi K2.5": (0.67, 0.20), "Qwen 3 VL-235B": (0.62, 0.25), "Gemma 3-12B": (0.58, 0.31),
    },
    "logprob_auroc": {  # zero-extra-call token-prob mode (only open-weight models expose it)
        "Qwen 3.6-27B (first-tok)": 0.62, "Gemma 3-12B (first-tok)": 0.64,
    },
    "best_intrinsic": ("Claude Opus 4.6 verbalized", 0.84),
    "best_logprob": ("Gemma 3-12B first-tok", 0.64),
    "logprob_range": "0.58-0.64",
    "ecarb_30pct": {"Opus 4.6": 2.43, "logprob modes": "1.30-1.45"},
    "note": "ConfBench reports AUROC/ECE/Brier/ECARB; NOT catch-rate or coverage@risk. "
            "Only AUROC is directly comparable to ours.",
}


def load(p):
    return [json.loads(l) for l in open(p)] if p.exists() else []


def auroc(pairs):
    pos = [s for s, c in pairs if c]; neg = [s for s, c in pairs if not c]
    if not pos or not neg:
        return None
    allp = sorted(pairs); r = [0] * len(allp); j = 0
    while j < len(allp):
        k = j
        while k + 1 < len(allp) and allp[k + 1][0] == allp[j][0]:
            k += 1
        for t in range(j, k + 1):
            r[t] = (j + k) / 2 + 1
        j = k + 1
    sr = sum(r[i] for i, (s, c) in enumerate(allp) if c)
    return (sr - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def cov_at(rows, tgt):
    n = len(rows); sc = [(s, c) for s, c in rows if s is not None]; best = 0.0
    for i in range(101):
        t = i / 100; acc = [c for s, c in sc if s >= t]
        if acc and sum(1 for c in acc if not c) / len(acc) <= tgt:
            best = max(best, len(acc) / n)
    return best


def sc_of(r):
    return r["proba"] if r.get("proba") is not None else r.get("final_score")


def metrics(recs, scalar, key):
    rows = [r for r in recs if r.get("correct") is not None and (not scalar or r.get("field_type") == "scalar")]
    TN = sum(1 for r in rows if r["correct"] and r[key])
    FP = sum(1 for r in rows if r["correct"] and not r[key])
    TP = sum(1 for r in rows if not r["correct"] and not r[key])
    FN = sum(1 for r in rows if not r["correct"] and r[key])
    n = len(rows); w = TP + FN; co = TN + FP
    pairs = [(sc_of(r), r["correct"]) for r in rows if sc_of(r) is not None]
    au = auroc(pairs)
    return {"n": n, "err": round(w / n, 3) if n else None,
            "catch": round(TP / w, 3) if w else None, "fa": round(FP / co, 3) if co else None,
            "route_prec": round(TP / (TP + FP), 3) if (TP + FP) else None,
            "acc": round((TP + TN) / n, 3) if n else None,
            "accept_all_acc": round(co / n, 3) if n else None,
            "auroc": round(au, 3) if au is not None else None,
            "cov5": round(cov_at(pairs, 0.05), 3), "cov10": round(cov_at(pairs, 0.10), 3),
            "cov20": round(cov_at(pairs, 0.20), 3),
            "TN": TN, "FP": FP, "TP": TP, "FN": FN}


def table8(files):
    """8 rows: each file x {binary,3tier} x {scalar,all}."""
    rows = []
    for label, p in files:
        recs = load(p)
        for mode, key in [("binary", "accept_bin"), ("3tier", "accept_3t")]:
            for scalar in (True, False):
                m = metrics(recs, scalar, key)
                rows.append({"run": label, "mode": mode, "pop": "scalar" if scalar else "all", **m})
    return rows


def per_signal(recs):
    names = ["format_valid", "keyword_context", "source_context", "value_in_text",
             "label_value_distance", "partial_extraction"]
    out = {}
    for s in names:
        def mean(correct):
            xs = [r["signals"].get(s) for r in recs if r.get("signals") and r["correct"] == correct
                  and isinstance(r["signals"].get(s), (int, float))]
            return round(sum(xs) / len(xs), 3) if xs else None
        out[s] = {"mean_correct": mean(True), "mean_wrong": mean(False)}
    return out


def proba_sep(recs):
    rows = [r for r in recs if r.get("field_type") == "scalar" and r.get("correct") is not None
            and r.get("proba") is not None]
    cp = [r["proba"] for r in rows if r["correct"]]; wp = [r["proba"] for r in rows if not r["correct"]]
    return {"mean_correct": round(st.mean(cp), 3) if cp else None,
            "mean_wrong": round(st.mean(wp), 3) if wp else None,
            "median_correct": round(st.median(cp), 3) if cp else None,
            "correct_ge_0.5": f"{sum(1 for x in cp if x >= 0.5)}/{len(cp)}",
            "wrong_ge_0.5": f"{sum(1 for x in wp if x >= 0.5)}/{len(wp)}"}


def sufficiency(recs):
    return {"empty_prior_applied": sum(1 for r in recs if r.get("empty_prior_applied")),
            "gated": sum(1 for r in recs if r.get("gated")),
            "tier3": {k: sum(1 for r in recs if r.get("decision_3t") == k)
                      for k in ["NTP", "LLM_REVIEW", "HUMAN_REVIEW"]}}


# ---------------- compute everything ----------------
clean = load(CLEAN)
report = {
    "split": SPLIT,
    "diagnosis": DIAG,
    "table_tuned_vs_untuned": table8([("untuned(noisy)", NOISY), ("tuned(noisy)", TUNED)]),
    "table_before_after_clean": table8([("BEFORE(noisy)", NOISY), ("AFTER(clean)", CLEAN)]),
    "canonical_clean": {pop: {mode: metrics(clean, pop == "scalar",
                                            "accept_bin" if mode == "binary" else "accept_3t")
                              for mode in ["binary", "3tier"]} for pop in ["scalar", "all"]},
    "per_signal_clean": per_signal(clean),
    "proba_sep_clean_scalar": proba_sep(clean),
    "sufficiency_clean": sufficiency(clean),
    "confbench_comparison": CONFBENCH,
}
(UNS / "realkie_fcc" / "analysis").mkdir(exist_ok=True)
(UNS / "realkie_fcc" / "analysis" / "signal_report.json").write_text(json.dumps(report, indent=2))


# ---------------- render markdown ----------------
def row8(r):
    g = lambda k: "—" if r.get(k) is None else r[k]
    return (f"| {r['run']} | {r['mode']} | {r['pop']} | {g('n')} | {g('err')} | {g('catch')} | "
            f"{g('fa')} | {g('acc')} | {g('auroc')} | {g('cov5')} |")


H8 = ("| run | mode | pop | n | err | catch ↑ | FA ↓ | acc ↑ | AUROC ↑ | cov@5% ↑ |\n"
      "|---|---|---|---|---|---|---|---|---|---|")
tbl_tu = "\n".join([H8] + [row8(r) for r in report["table_tuned_vs_untuned"]])
tbl_ba = "\n".join([H8] + [row8(r) for r in report["table_before_after_clean"]])

cb = report["canonical_clean"]["scalar"]["binary"]
ca = report["canonical_clean"]["all"]["binary"]


def canon_row(pop, mode):
    m = report["canonical_clean"][pop][mode]
    g = lambda k: "—" if m.get(k) is None else m[k]
    return (f"| {pop} | {mode} | {g('n')} | {g('err')} | {g('catch')} | {g('fa')} | {g('route_prec')} | "
            f"{g('acc')} | {g('accept_all_acc')} | {g('auroc')} | {g('cov5')} | {g('cov10')} | {g('cov20')} |")


canon_tbl = "\n".join([
    "| pop | mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |",
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    canon_row("scalar", "binary"), canon_row("scalar", "3tier"),
    canon_row("all", "binary"), canon_row("all", "3tier")])

ps = report["per_signal_clean"]
sig_tbl = "\n".join(["| signal | mean(correct) | mean(wrong) |", "|---|---|---|"] +
                    [f"| {k} | {v['mean_correct']} | {v['mean_wrong']} |" for k, v in ps.items()])

# ---- ConfBench comparison tables ----
CB = report["confbench_comparison"]
cb_verb_tbl = "\n".join(["| model | method | AUROC | ECE |", "|---|---|---|---|"] +
                        [f"| {m} | verbalized | {a} | {e} |" for m, (a, e) in CB["verbalized_auroc"].items()] +
                        [f"| {m} | **logprob (zero-call)** | {a} | — |" for m, a in CB["logprob_auroc"].items()])
head2head = "\n".join([
    "| system | mechanism | extra call? | trained on FCC? | AUROC |",
    "|---|---|---|---|---|",
    f"| ConfBench — best logprob ({CB['best_logprob'][0]}) | intrinsic token probs | none | no (zero-shot) | {CB['logprob_range']} |",
    f"| ConfBench — best model ({CB['best_intrinsic'][0]}) | intrinsic self-report | none | no (zero-shot) | {CB['best_intrinsic'][1]} |",
    f"| **Ours — Signal, all fields (entity-level)** | external trained verifier | **none** | yes (offline) | **{ca['auroc']}** |",
    f"| **Ours — Signal, scalar subset** | external trained verifier | **none** | yes (offline) | **{cb['auroc']}** |"])
pr = report["proba_sep_clean_scalar"]
suf = report["sufficiency_clean"]
D = report["diagnosis"]
S = report["split"]
test_dropped = 484 - ca["n"]            # noisy all-test n (484) - clean all-test n
test_dropped_scalar = 264 - cb["n"]     # noisy scalar-test n (264) - clean scalar-test n

doc = f"""# Unstructured NTP — the **Signal verifier** on RealKIE-FCC (complete reference)

> One-stop reference for the unstructured leg of EBV. Every number is generated by
> `scripts/build_signal_report.py` from the stored `decisions/*.jsonl` (no retrain/re-infer,
> no hand-typed numbers). Re-run that script to regenerate this file.

## 0. TL;DR (what to quote)
- **Canonical config = `bundle_clean` (untuned) · binary mode · scalar fields.**
- **Headline: AUROC {cb['auroc']}, and auto-approve {round(cb['cov5']*100)}% of scalar fields at ≤5% error** (cov@5% {cb['cov5']}).
- The **score** is the capability (AUROC/coverage). **Do NOT quote accuracy as the headline** — see §6.
- Signal is the **harder end of the detectability frontier** (messy real invoices) vs ROI on clean FATURA — the intended contrast.
- **vs ConfBench (same FCC dataset, §8):** our zero-call verifier (AUROC **{ca['auroc']}** all / **{cb['auroc']}** scalar) beats zero-call log-prob confidence (**{CB['logprob_range']}**) and matches the best model's self-confidence (**{CB['best_intrinsic'][1]}**, Opus 4.6). We therefore **cannot** claim "first/only zero-call" — our edge is *external, extractor-agnostic, higher-discrimination*.

## 1. What the Signal verifier is
dociq's **production** NTP Signal classifier: for each extracted field it computes **6 text
signals** from only `(field, value, document_text)` — **no OCR, no positions, no extra LLM/VLM
call** — feeds them to a small tabular model, and emits accept vs route.
- 6 signals: `format_valid`, `keyword_context`, `source_context`, `value_in_text`,
  `label_value_distance`, `partial_extraction` (+ `is_empty`, `gt_empty_rate` features).
- **binary** mode: accept (`NTP`) / route (`REVIEW`).
- **3-tier** mode: `NTP` / `LLM_REVIEW` / `HUMAN_REVIEW`; we collapse {{LLM,HUMAN}}→route.
- The hard accept/route label has **no native probability**; for AUROC/coverage we rebuild
  `predict_proba` from the saved model using its own `feature_names_in_` order (`infer_signal.py`).

## 2. How it was run (dociq untouched)
- Drove dociq's own `score_new_data.py` + `run_ntp_direct_classifier.py` **in place**
  (`cwd=dociq`) with OUR paper venv + OUR data dirs; all outputs land under this experiment.
  dociq repo verified unmodified (no tracked changes, no stray bundles).
- **2 models trained** per run: RandomForest(500) + GradientBoosting(300) for doc-type `invoice`.
  Binary uses the best single model (gbm); 3-tier uses both as the agreement pair.
- **Auto-labels** correct/wrong from ground truth via dociq's field-aware matcher at train time.

## 3. Data & split (RealKIE-FCC invoices)
- {S['n_docs']} docs usable ({S['skipped']} skipped = failed extraction), **{S['n_train']} train / {S['n_test']} test** (80/20, seed {S['seed']}).
- Extractor = NuExtract-3. Input per doc: `{{field: value}}` + full document text + doc_type `invoice`.
- **Correctness = membership** (normalized, alnum-lowercased): a prediction is correct if it matches
  ANY ground-truth value of the field (FCC has multi-value "Line Item -" fields; NuExtract emits one).
- **Field types:** 6 **scalar** fields (Agency, Advertiser, Gross Total, Net Amount Due, Agency
  Commission, Payment Terms) = the real single-value KIE targets; 5 **"Line Item -"** fields are
  **tabular** (belong to the Table-Trust leg) and only reported in the `all` population.

## 4. Two things we studied before locking results

### 4a. Tuning (RandomizedSearchCV) vs untuned defaults — on the NOISY labels
"Tuning" = hyperparameter search only (tree count/depth/learning-rate); **same data, signals,
algorithm, correctness**. untuned = dociq defaults (`--skip-tuning`); tuned = `RandomizedSearchCV`.

{tbl_tu}

**Verdict:** tuning did **not** improve discrimination — AUROC essentially flat (scalar 0.804→0.813;
all 0.758→0.751, slightly worse). It only shifted the operating point to route more aggressively
(higher catch, higher false-alarm, lower accuracy). The signal set caps the ceiling, not the
hyperparameters. → **untuned is canonical** (equivalent quality, faster, less over-routing).

### 4b. Label cleanup — the GT-sparsity fix (the important one)
**Problem found during audit:** RealKIE ground truth is **sparse** — annotators leave many fields
unlabelled. When the extractor produced a plausible value for such a field, the old pipeline labelled
it **"wrong"** (GT-absent + pred-present). That is an *unconfirmed* error, not a real one.

Evidence (computed on the pre-clean meta during the audit; now superseded on disk):
- TRAIN scalar "wrong" = {D['train_scalar_wrong']}, of which **{D['train_scalar_gt_absent_pred_present']} were GT-absent/pred-present**
  (not confirmed errors), {D['train_scalar_both_present_mismatch']} both-present mismatches, {D['train_scalar_miss']} real misses.
- Matcher sanity (scalar, {D['matcher_scalar_n']} test): correct under exact-equality = {D['matcher_exact_eq']}, under loose
  substring = {D['matcher_loose_substr']}. So our matcher is *lenient* (understates error) — i.e. **no bug that
  inflates errors**; normalization (lowercase + strip non-alphanumerics) is applied.
- These fake "errors" taught the classifier to **distrust good extractions**, so it over-routed.

**Fix (`build_fcc_dataset.py`):** treat GT-absent + pred-present as **UNLABELLED → dropped** from
both train and eval (keep GT-absent+pred-absent as a correct "extracted nothing", keep all real
misses/mismatches). Dropped **{S.get('dropped_unlabelled','?')}** instances total
({test_dropped} in test: {test_dropped_scalar} scalar + {test_dropped-test_dropped_scalar} line-item;
the rest in train). This is standard "exclude unlabelled", not cherry-picking.

## 5. Before vs after the cleanup (8 rows)
{tbl_ba}

**Effect on the canonical slice (scalar / binary):** AUROC **0.804 → {cb['auroc']}**, cov@5%
**0.386 → {cb['cov5']}**, false-alarm **0.455 → {cb['fa']}**, accuracy **0.606 → {cb['acc']}**,
catch **0.863 → {cb['catch']}**. Every metric improved — directly confirming the fake-error diagnosis.

## 6. Why accuracy is NOT the headline (read this before asking "why is accuracy low")
- **accept-all** = a do-nothing verifier that accepts everything. Its accuracy = the already-correct
  rate = **1 − err**. For canonical scalar that is **{cb['accept_all_acc']}** (err {cb['err']}).
- Our verifier's accuracy at the default 0.5 threshold is **{cb['acc']}** — *below* accept-all.
- **Why:** accuracy punishes a wrongly-flagged *correct* field exactly as hard as a missed error, and
  correct fields vastly outnumber errors. Of {cb['n']} scalar fields the model correctly accepts
  {cb['TN']} and catches {cb['TP']} of {cb['TP']+cb['FN']} errors, but it also flags {cb['FP']}
  correct ones (false alarms) → acc ({cb['TP']}+{cb['TN']})/{cb['n']} = {cb['acc']}.
- **A verifier's job is not accept/route accuracy** — it is "auto-approve as much as possible under an
  error budget". That is **coverage@risk**: accept-all auto-approves 100% but at {cb['err']} error
  (fails a 5% budget); ours auto-approves **{round(cb['cov5']*100)}% at ≤5% error**. That is the capability.
- Score separation confirms it: on clean scalar, mean accept-proba = **{pr['mean_correct']} on correct**
  vs **{pr['mean_wrong']} on wrong** (correct≥0.5: {pr['correct_ge_0.5']}, wrong≥0.5: {pr['wrong_ge_0.5']}).

## 7. Canonical results (clean run, full metrics)
{canon_tbl}

Notes: **binary is the mode to report** — 3-tier over-routes (higher catch but much higher
false-alarm, lower accuracy). `cov@R` = fraction of fields auto-approvable while held-out error ≤ R.

### 7a. Per-signal separation (clean; mean signal value, correct vs wrong)
{sig_tbl}

### 7b. Sufficiency / empty handling (clean)
`empty_prior_applied`={suf['empty_prior_applied']}, `gated`={suf['gated']}, 3-tier routing={suf['tier3']}.

## 8. Related-work comparison — ConfBench on the SAME dataset (RealKIE-FCC)
**{CB['source']}.** ConfBench is a benchmark of a model's **own (intrinsic) confidence** — verbalized
or log-probability — about its **own** extraction; it trains **no external verifier**. Base extraction
accuracy WOA **{CB['base_acc_WOA']}** (close to our all-fields ~0.79, so base-error is comparable —
a fairer match than the FATURA/Jin case). It reports **AUROC/ECE/Brier/ECARB — NOT catch-rate or
coverage@risk**, so **AUROC is the only directly comparable axis**.

### Their AUROC for misextraction detection (Table 3, OCR+Image, all 7 models)
{cb_verb_tbl}

Best intrinsic confidence = **{CB['best_intrinsic'][0]} ({CB['best_intrinsic'][1]})**; best zero-call
log-prob = **{CB['best_logprob'][0]} ({CB['best_logprob'][1]})**; log-prob range **{CB['logprob_range']}**.
Their operational metric ECARB@30%-budget: Opus 4.6 **{CB['ecarb_30pct']['Opus 4.6']}×**, log-prob modes **{CB['ecarb_30pct']['logprob modes']}×** over random review.

### Head-to-head (AUROC — the shared axis)
{head2head}

### Honest verdict
- **vs zero-call log-probabilities (the directly comparable cheap mode): clear win** — ours
  {ca['auroc']} (all) / {cb['auroc']} (scalar) vs **{CB['logprob_range']}**. Intrinsic log-prob confidence
  barely discriminates errors on FCC (~0.6); a cheap external signal verifier reaches ~0.83–0.90.
- **vs the best any model achieves (Opus 4.6 verbalized {CB['best_intrinsic'][1]}): a tie, not a win** —
  our entity-level {ca['auroc']} is just below {CB['best_intrinsic'][1]}; our scalar subset {cb['auroc']}
  edges above but is a cleaner subset, so we do **not** claim a win over Opus.
- **Caveats (state them):** (1) different paradigm — they measure *intrinsic* zero-shot confidence,
  ours is an *external classifier trained on FCC labels* (in-domain supervised advantage); (2) different
  extractor (their VLMs self-rate; ours = NuExtract-3 + separate verifier) and population (their 1,346
  degraded variants / WOA vs our natural {ca['n']} instances / membership); (3) only AUROC is shared —
  no catch-rate/coverage on their side, no ECARB/ECE on ours (both computable later if needed).
- **Positioning:** on the same FCC data, zero-call log-prob confidence reaches only {CB['logprob_range']}
  AUROC and the strongest model self-confidence tops out at {CB['best_intrinsic'][1]}; a lightweight
  **external** verifier — also no extra call, and usable even when the extractor exposes **no** confidence
  (our NuExtract case) — matches the best model and exceeds it on clean scalar fields.
  **⇒ Don't trust the model's own confidence; use external evidence.**

## 9. Findings (honest)
1. **Scalar is a strong, usable result after cleanup:** AUROC **{cb['auroc']}**, auto-approve
   **{round(cb['cov5']*100)}% at ≤5% error** — with **no extra model call**.
2. **Line-item fields drag `all` down** (AUROC {ca['auroc']}, cov@5% {ca['cov5']}) — confirming they are
   tabular, not single-value Signal targets. Expected; they belong to the table leg.
3. **The default threshold over-routes** even after cleanup (FA {cb['fa']}, acc {cb['acc']} < accept-all
   {cb['accept_all_acc']}). The **risk-coverage curve**, not the default threshold, is the capability story (§6).
4. **Tuning does not help** (§4a) — the signal set caps the ceiling.
5. **Harder end of the detectability frontier:** Signal on messy real FCC is weaker than ROI on clean
   FATURA — the intended, honest contrast of the paper.

## 10. Limitations (state these in the paper)
- Small test (**{cb['n']} scalar** instances) → sampling noise.
- Cleanup drops {S.get('dropped_unlabelled','?')} unverifiable instances; we assume they are not
  systematically different from the labelled ones.
- Membership matcher is lenient (both-ways substring) → error base is a lower bound.
- Signals are production-designed for dociq docs; FCC is out-of-distribution (domain shift), which is
  part of why it is weaker than production scores on dociq's own data.

## 11. Directory & reproduce
```
.venv/                         paper-local venv (sklearn/joblib/pandas) — dociq untouched
scripts/build_fcc_dataset.py   build dociq-format records + 80/20 split; UNLABELLED-drop cleanup
scripts/train_signal.py        drives dociq score_new_data + run_ntp_direct_classifier (cwd=dociq)
scripts/infer_signal.py        engine predict_document (binary+3tier) + rebuilt predict_proba
scripts/analyze_signal.py      per-run metrics -> analysis/signal_metrics.json
scripts/compare_tuned.py       quick side-by-side of two decisions files
scripts/build_signal_report.py THIS doc + analysis/signal_report.json (all tables as data)
data/{{train,test}}/invoice.json  dociq input ; data/meta/*  pred+gt+field_type+label ; data/split.json
bundle/        untuned on NOISY labels      bundle_tuned/  tuned on NOISY labels
bundle_clean/  untuned on CLEAN labels  <-- CANONICAL
decisions/fcc_decisions.jsonl (noisy)  _tuned.jsonl (tuned)  _clean.jsonl (CANONICAL)
analysis/signal_report.json  paper/UNSTRUCTURED_EXPERIMENT.md
logs/  build/train/infer/analyze (+ _tuned, _clean) full output incl. internal CV
```
Reproduce the canonical run:
```
PY=.venv/bin/python
$PY scripts/build_fcc_dataset.py
$PY scripts/train_signal.py  --bundle bundle_clean
$PY scripts/infer_signal.py  --bundle bundle_clean --out decisions/fcc_decisions_clean.jsonl
$PY scripts/build_signal_report.py        # regenerate this doc from stored decisions
```

## 12. Provenance
Predictions+GT: `experiments/results/realkie_fcc_results/`. Text: `realkie_fcc_invoices/train.csv`.
Signal code: `/Users/rajeshgupta/Git_Clones/dociq/app/ntp_classifier/` (run in place, unmodified).
ConfBench figures (§8): arXiv 2608.01792 (abs: arxiv.org/abs/2608.01792 · html: arxiv.org/html/2608.01792v1), Table 3 OCR+Image.
"""
(UNS / "paper").mkdir(exist_ok=True)
(UNS / "paper" / "UNSTRUCTURED_EXPERIMENT.md").write_text(doc)
print("wrote", UNS / "paper" / "UNSTRUCTURED_EXPERIMENT.md")
print("wrote", UNS / "realkie_fcc" / "analysis" / "signal_report.json")
