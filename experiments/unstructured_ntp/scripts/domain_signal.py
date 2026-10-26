#!/usr/bin/env python3
"""
Generalized Signal-NTP experiment driver for ANY RealKIE domain (charities / nda / s1),
reproducing the exact FCC matrix (see paper/UNSTRUCTURED_EXPERIMENT.md) without touching
the original FCC scripts or the dociq repo.

For a given --dataset it:
  1. builds the dociq-format input TWICE — `clean` (GT-sparsity fix: drop unlabelled
     GT-absent+pred-present) and `noisy` (label those as wrong, the pre-fix behaviour);
  2. trains 3 bundles by driving dociq's own score_new_data.py + run_ntp_direct_classifier.py
     in place (cwd=dociq, OUR paper venv): bundle_clean (clean,untuned=CANONICAL),
     bundle (noisy,untuned), bundle_tuned (noisy,tuned=RandomizedSearchCV);
  3. infers each bundle on its own held-out test split via dociq's NTPInferenceEngine
     (binary + 3tier) + a rebuilt predict_proba (model feature order);
  4. analyzes every decisions file -> metrics (catch/FA/route-prec/acc/AUROC/cov@risk,
     per-signal separation, 3-tier breakdown).

Everything lands under experiments/unstructured_ntp/<dataset>/. dociq untouched.

Usage:
  domain_signal.py --dataset realkie_nda [--steps build,train,infer,analyze] [--skip-tuning-bundle]
"""
from __future__ import annotations
import argparse, csv, json, random, re, subprocess, sys
from pathlib import Path

csv.field_size_limit(10**7)
EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
UNS = EBV / "experiments" / "unstructured_ntp"
PY = str(UNS / ".venv" / "bin" / "python")
DOCIQ_NTP = Path("/Users/rajeshgupta/Git_Clones/dociq/app/ntp_classifier")
SEED, TRAIN_FRAC = 42, 0.80
_ALNUM = re.compile(r"[^a-z0-9]+")

# dataset -> (dataset dir name, results subdir, doc_type label)
DOMAINS = {
    "realkie_charities": ("realkie_charities", "realkie_charities_results", "charity_report"),
    "realkie_nda":       ("realkie_nda",       "realkie_nda_results",       "nda"),
    "realkie_s1":        ("realkie_s1",        "realkie_s1_results",        "s1_filing"),
    # FCC is kept here too so the generalized path can reproduce the canonical leg if wanted.
    "realkie_fcc":       ("realkie_fcc_invoices", "realkie_fcc_results",    "invoice"),
}


# --------------------------------------------------------------------------- #
# helpers (ported verbatim-in-spirit from build_fcc_dataset / infer / analyze)
# --------------------------------------------------------------------------- #
def norm(s):
    return _ALNUM.sub("", str(s).lower()) if s is not None else ""


def membership(pred, gt, keep_noisy: bool):
    """(status, gt_string). status True=correct False=wrong None=UNLABELLED(drop).
    keep_noisy=True reproduces the pre-fix behaviour: GT-absent+pred-present -> wrong."""
    cands = gt if isinstance(gt, list) else ([] if gt is None else [gt])
    cands = [c for c in cands if c is not None and str(c).strip() != ""]
    p = norm(pred)
    if not cands:                        # GT empty/absent
        if p == "":
            return (True, "")
        return ((False, "") if keep_noisy else (None, ""))   # pred present, GT unconfirmed
    if p == "":
        return (False, str(cands[0]))
    for c in cands:
        nc = norm(c)
        if nc and (p == nc or p in nc or nc in p):
            return (True, str(c))
    return (False, str(cands[0]))


def text_map(ds_dir: Path):
    """doc_id -> document text, with the SAME id/dedup convention as datasets.RealKieAdapter
    (base = original_filename stem; duplicates get __pN) so ids match extraction_results."""
    m, seen = {}, {}
    with open(ds_dir / "train.csv", newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            base = Path(row.get("original_filename") or f"doc_{i}").stem
            n = seen.get(base, 0); seen[base] = n + 1
            doc_id = base if n == 0 else f"{base}__p{n}"
            m[doc_id] = row.get("text") or ""
    return m


def build(dataset: str, mode: str, root: Path, ds_dir: Path, res_dir: Path, doc_type: str):
    """mode in {'clean','noisy'}. Writes data_<mode>/{train,test,meta} + split.json."""
    keep_noisy = (mode == "noisy")
    tmap = text_map(ds_dir)
    gt_all = json.loads((res_dir / f"ground_truth_{dataset}.json").read_text())
    res_all = json.loads((res_dir / f"extraction_results_{dataset}.json").read_text())
    ext = next(iter(next(iter(res_all.values())).keys()))

    records, meta = [], {}
    skipped = dropped = 0
    for doc_id, blob in res_all.items():
        pred = (blob.get(ext, {}).get("extracted")) or {}
        if blob.get(ext, {}).get("metrics", {}).get("error") or not pred:
            skipped += 1; continue
        text = tmap.get(doc_id, "")
        if not text:
            skipped += 1; continue
        gt = gt_all.get(doc_id, {})
        ner, entities, mfields = {}, [], {}
        for f in sorted(set(pred) | set(gt)):
            pv = pred.get(f)
            status, gt_str = membership(pv, gt.get(f), keep_noisy)
            if status is None:
                dropped += 1; continue
            ner[f] = "" if pv is None else str(pv)
            entities.append({"fieldName": f, "groundTruth": gt_str})
            mfields[f] = {"pred": pv, "gt": gt.get(f),
                          "field_type": "lineitem" if f.lower().startswith("line item") else "scalar",
                          "member_correct": status}
        records.append({"documentId": doc_id, "text": text, "NER_Output": ner, "entities": entities})
        meta[doc_id] = mfields

    ids = sorted(meta)
    rng = random.Random(SEED); rng.shuffle(ids)
    n_tr = round(TRAIN_FRAC * len(ids))
    train_ids, test_ids = set(ids[:n_tr]), set(ids[n_tr:])
    tr = [r for r in records if r["documentId"] in train_ids]
    te = [r for r in records if r["documentId"] in test_ids]

    data = root / f"data_{mode}"
    for sub in ("train", "test", "meta"):
        (data / sub).mkdir(parents=True, exist_ok=True)
    (data / "train" / f"{doc_type}.json").write_text(json.dumps(tr))
    (data / "test" / f"{doc_type}.json").write_text(json.dumps(te))
    (data / "meta" / "train_meta.json").write_text(json.dumps({d: meta[d] for d in train_ids}))
    (data / "meta" / "test_meta.json").write_text(json.dumps({d: meta[d] for d in test_ids}))
    n_fields = sum(len(m) for m in meta.values())
    n_scalar = sum(1 for m in meta.values() for v in m.values() if v["field_type"] == "scalar")
    (data / "split.json").write_text(json.dumps(
        {"mode": mode, "seed": SEED, "train_frac": TRAIN_FRAC, "n_docs": len(records),
         "n_train": len(tr), "n_test": len(te), "skipped": skipped, "dropped_unlabelled": dropped,
         "n_field_instances": n_fields, "n_scalar": n_scalar, "n_lineitem": n_fields - n_scalar,
         "train_ids": sorted(train_ids), "test_ids": sorted(test_ids)}, indent=2))
    print(f"[build {dataset}/{mode}] docs={len(records)} (skipped {skipped}) "
          f"train {len(tr)}/test {len(te)} | field_inst={n_fields} scalar={n_scalar} "
          f"lineitem={n_fields-n_scalar} dropped_unlabelled={dropped}")


def _run(cmd):
    print("+", " ".join(str(c) for c in cmd), f"(cwd={DOCIQ_NTP})")
    r = subprocess.run([str(c) for c in cmd], cwd=str(DOCIQ_NTP))
    if r.returncode != 0:
        sys.exit(f"FAILED (exit {r.returncode}): {' '.join(str(c) for c in cmd)}")


def train(root: Path, data_mode: str, bundle_name: str, doc_type: str, tune: bool):
    data = root / f"data_{data_mode}"
    scored = root / f"scored_{data_mode}"
    bundle = root / bundle_name
    scored.mkdir(parents=True, exist_ok=True); bundle.mkdir(parents=True, exist_ok=True)
    _run([PY, DOCIQ_NTP / "score_new_data.py", "--input-dir", data / "train",
          "--output-dir", scored, "--doc-types", doc_type])
    cmd = [PY, DOCIQ_NTP / "run_ntp_direct_classifier.py", "--input-dir", scored,
           "--output-dir", bundle, "--auto-signals", "--models", "rf", "gbm", "--doc-types", doc_type]
    if not tune:
        cmd.append("--skip-tuning")
    _run(cmd)
    print(f"[train] bundle -> {bundle.name} (data={data_mode}, tuning={'ON' if tune else 'OFF'})")


def _sig_val(v):
    if v is None:
        return -1.0
    if isinstance(v, bool):
        return 0.0 if v is False else -1.0
    try:
        return float(v)
    except Exception:
        return -1.0


def infer(root: Path, data_mode: str, bundle_name: str, doc_type: str, out_path: Path):
    import joblib, pandas as pd
    sys.path.insert(0, str(DOCIQ_NTP))
    from ntp_inference import NTPInferenceEngine  # noqa: E402

    data = root / f"data_{data_mode}"
    bundle = root / bundle_name
    TEST = json.loads((data / "test" / f"{doc_type}.json").read_text())
    META = json.loads((data / "meta" / "test_meta.json").read_text())
    model = joblib.load(bundle / "models" / f"best_model_{doc_type}.joblib")
    feats = list(model.feature_names_in_)
    prior_raw = json.loads((bundle / "field_gt_empty_prior.json").read_text())
    prior = prior_raw.get(doc_type, prior_raw) if isinstance(prior_raw, dict) else {}
    pos = list(model.classes_).index(1) if 1 in list(getattr(model, "classes_", [1])) else 1

    def proba(signals, field, value):
        try:
            is_empty = 1.0 if (value is None or str(value).strip() == "") else 0.0
            ger = prior.get(field, {}).get("gt_empty_rate", -1.0)
            rowv = {}
            for name in feats:
                if name == "is_empty":
                    rowv[name] = is_empty
                elif name == "gt_empty_rate":
                    rowv[name] = float(ger) if ger is not None else -1.0
                else:
                    rowv[name] = _sig_val((signals or {}).get(name))
            return float(model.predict_proba(pd.DataFrame([rowv], columns=feats))[0, pos])
        except Exception:
            return None

    engine = NTPInferenceEngine(model_dir=str(bundle / "models"), config_dir=str(bundle))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out_path, "w") as out:
        for rec in TEST:
            doc = rec["documentId"]; ner = rec["NER_Output"]; text = rec["text"]
            rb = engine.predict_document(ner, text, doc_type, mode="binary")
            try:
                r3 = engine.predict_document(ner, text, doc_type, mode="3tier")
            except Exception:
                r3 = {"fields": {}}
            for f, fr in rb.get("fields", {}).items():
                m = META.get(doc, {}).get(f, {})
                dec_bin = fr.get("decision")
                dec_3t = r3.get("fields", {}).get(f, {}).get("decision")
                out.write(json.dumps({
                    "doc": doc, "field": f, "field_type": m.get("field_type"),
                    "correct": m.get("member_correct"),
                    "decision_bin": dec_bin, "accept_bin": dec_bin == "NTP",
                    "decision_3t": dec_3t, "accept_3t": dec_3t == "NTP",
                    "final_score": fr.get("final_score"),
                    "proba": proba(fr.get("signals"), f, fr.get("value", ner.get(f))),
                    "gt_empty_rate": fr.get("gt_empty_rate"),
                    "empty_prior_applied": fr.get("empty_prior_applied"),
                    "gated": fr.get("gated"), "signals": fr.get("signals"),
                }, default=str) + "\n")
                n += 1
    print(f"[infer] {n} field decisions over {len(TEST)} docs (bundle={bundle_name}) -> {out_path}")


# --------------------------- analysis (ported from analyze_signal.py) -------- #
def _auroc(pairs):
    pos = [s for s, c in pairs if c]; neg = [s for s, c in pairs if not c]
    if not pos or not neg:
        return None
    allp = sorted(pairs, key=lambda x: x[0]); r = [0] * len(allp); j = 0
    while j < len(allp):
        k = j
        while k + 1 < len(allp) and allp[k + 1][0] == allp[j][0]:
            k += 1
        for t in range(j, k + 1):
            r[t] = (j + k) / 2 + 1
        j = k + 1
    sr = sum(r[i] for i, (s, c) in enumerate(allp) if c)
    return (sr - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def _cov_at_risk(rows, targets=(0.05, 0.10, 0.20)):
    n = len(rows); scored = [(s, c) for s, c in rows if s is not None]
    out = {}
    for tgt in targets:
        best = 0.0
        for i in range(101):
            t = i / 100; acc = [c for s, c in scored if s >= t]
            if acc and sum(1 for c in acc if not c) / len(acc) <= tgt:
                best = max(best, len(acc) / n)
        out[tgt] = best
    return out


def _score_of(r):
    return r["proba"] if r.get("proba") is not None else r.get("final_score")


def _confusion(rows, accept_key):
    TN = sum(1 for r in rows if r["correct"] and r[accept_key])
    FP = sum(1 for r in rows if r["correct"] and not r[accept_key])
    TP = sum(1 for r in rows if not r["correct"] and not r[accept_key])
    FN = sum(1 for r in rows if not r["correct"] and r[accept_key])
    n = TN + FP + TP + FN; w = TP + FN; co = TN + FP
    sc = [(_score_of(r), r["correct"]) for r in rows if _score_of(r) is not None]
    cov = _cov_at_risk([(_score_of(r), r["correct"]) for r in rows])
    return {"n": n, "wrong": w, "err_rate": round(w / n, 4) if n else None,
            "error_catch": round(TP / w, 4) if w else None,
            "false_alarm": round(FP / co, 4) if co else None,
            "route_prec": round(TP / (TP + FP), 4) if (TP + FP) else None,
            "accuracy": round((TP + TN) / n, 4) if n else None,
            "accept_all_acc": round(1 - (w / n), 4) if n else None,
            "AUROC": round(_auroc(sc), 4) if _auroc(sc) is not None else None,
            "cov@5%": round(cov[0.05], 4), "cov@10%": round(cov[0.10], 4), "cov@20%": round(cov[0.20], 4)}


def analyze(decisions_path: Path):
    RECS = [json.loads(l) for l in open(decisions_path)]
    out = {}
    for pop, filt in [("all", lambda r: True), ("scalar", lambda r: r.get("field_type") == "scalar")]:
        rows = [r for r in RECS if filt(r) and r.get("correct") is not None]
        out[pop] = {"binary": _confusion(rows, "accept_bin"), "3tier": _confusion(rows, "accept_3t")}
    out["sufficiency"] = {
        "empty_prior_applied": sum(1 for r in RECS if r.get("empty_prior_applied")),
        "gated": sum(1 for r in RECS if r.get("gated")),
        "tier3_breakdown": {k: sum(1 for r in RECS if r.get("decision_3t") == k)
                            for k in ["NTP", "LLM_REVIEW", "HUMAN_REVIEW"]},
    }
    persig = {}
    for s in ["format_valid", "keyword_context", "source_context", "value_in_text",
              "label_value_distance", "partial_extraction"]:
        def vals(correct):
            xs = [r["signals"].get(s) for r in RECS if r.get("signals") and r["correct"] == correct
                  and isinstance(r["signals"].get(s), (int, float))]
            return round(sum(xs) / len(xs), 3) if xs else None
        persig[s] = {"mean_correct": vals(True), "mean_wrong": vals(False)}
    out["per_signal_mean"] = persig
    return out


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=list(DOMAINS))
    ap.add_argument("--steps", default="build,train,infer,analyze")
    ap.add_argument("--bundles", default="clean,noisy,tuned",
                    help="which run tags to train/infer/analyze (clean,noisy,tuned)")
    a = ap.parse_args()
    steps = set(a.steps.split(","))
    want = set(a.bundles.split(","))
    ds_name, res_sub, doc_type = DOMAINS[a.dataset]
    ds_dir = EBV / ds_name
    res_dir = EBV / "experiments" / "results" / res_sub
    root = UNS / a.dataset
    root.mkdir(parents=True, exist_ok=True)
    (root / "decisions").mkdir(exist_ok=True)
    (root / "analysis").mkdir(exist_ok=True)

    # (data_mode, bundle_name, tune, decisions_tag)
    runs = [r for r in [("clean", "bundle_clean", False, "clean"),
                        ("noisy", "bundle",       False, "noisy"),
                        ("noisy", "bundle_tuned", True,  "tuned")]
            if r[3] in want]

    if "build" in steps:
        for dm in sorted({r[0] for r in runs}):
            build(a.dataset, dm, root, ds_dir, res_dir, doc_type)
    if "train" in steps:
        for data_mode, bundle_name, tune, _ in runs:
            train(root, data_mode, bundle_name, doc_type, tune)
    if "infer" in steps:
        for data_mode, bundle_name, _, tag in runs:
            dp = root / "decisions" / f"{a.dataset}_{tag}.jsonl"
            if dp.exists() and dp.stat().st_size > 0:
                print(f"[infer] skip {tag}: decisions already present ({dp})"); continue
            if not (root / bundle_name / "models" / f"best_model_{doc_type}.joblib").exists():
                print(f"[infer] skip {bundle_name}: no trained model"); continue
            infer(root, data_mode, bundle_name, doc_type, dp)
    if "analyze" in steps:
        metrics = {}
        for _, _, _, tag in runs:
            dp = root / "decisions" / f"{a.dataset}_{tag}.jsonl"
            if dp.exists():
                metrics[tag] = analyze(dp)
        splits = {m: json.loads((root / f"data_{m}" / "split.json").read_text())
                  for m in ("clean", "noisy") if (root / f"data_{m}" / "split.json").exists()}
        (root / "analysis" / "signal_metrics.json").write_text(
            json.dumps({"dataset": a.dataset, "doc_type": doc_type,
                        "splits": splits, "metrics": metrics}, indent=2))
        print(f"[analyze] -> {root/'analysis'/'signal_metrics.json'}")


if __name__ == "__main__":
    main()
