"""E2 Signal drop-one ablation. Replicate the production feature set (8 features: 6 signals +
is_empty + gt_empty_rate), train a GBM, RECONCILE its AUROC to the production proba (FCC 0.897 /
pooled 0.955); if it reconciles, report full vs drop-one AUROC per channel. Else fall back to the
production feature importances (already reported). doc-grouped 5-fold CV."""
import json, re, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(__file__)); import lib_frontier as L
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import GroupKFold
U = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/unstructured_ntp"
DOMS = {"FCC": (f"{U}/realkie_fcc/decisions/fcc_decisions_clean.jsonl", f"{U}/realkie_fcc/data/test/invoice.json", f"{U}/realkie_fcc/bundle_clean/field_gt_empty_prior.json", "invoice"),
        "S1": (f"{U}/realkie_s1/decisions/realkie_s1_clean.jsonl", f"{U}/realkie_s1/data_clean/test/s1_filing.json", f"{U}/realkie_s1/bundle_clean/field_gt_empty_prior.json", "s1_filing"),
        "Charities": (f"{U}/realkie_charities/decisions/realkie_charities_clean.jsonl", f"{U}/realkie_charities/data_clean/test/charity_report.json", f"{U}/realkie_charities/bundle_clean/field_gt_empty_prior.json", "charity_report")}
SIG = ["format_valid", "keyword_context", "source_context", "value_in_text", "label_value_distance", "cross_field_copy"]
FEATS = SIG + ["is_empty", "gt_empty_rate"]
def num(x):
    if x is True: return 1.0
    if x is False: return 0.0
    if x is None: return np.nan
    try: return float(x)
    except: return np.nan
rows = []
for name, (decf, dataf, priorf, dt) in DOMS.items():
    data = {d["documentId"]: (d.get("NER_Output") or {}) for d in json.load(open(dataf))}
    prior = json.load(open(priorf)) if os.path.exists(priorf) else {}
    pr = prior.get(dt, prior)
    for ln in open(decf):
        o = json.loads(ln)
        if o.get("field_type") != "scalar": continue
        s = o.get("signals") or {}
        pred = data.get(o["doc"], {}).get(o["field"])
        ger = o.get("gt_empty_rate")
        if ger is None:
            fp = pr.get(o["field"]); ger = fp.get("gt_empty_rate") if isinstance(fp, dict) else None
        r = {"doc": o["doc"], "correct": int(bool(o["correct"])),
             "is_empty": 1.0 if (pred is None or str(pred).strip() == "") else 0.0,
             "gt_empty_rate": num(ger) if ger is not None else 0.0}
        for c in SIG: r[c] = num(s.get(c))
        rows.append(r)
import pandas as pd
df = pd.DataFrame(rows); print(f"n={len(df)}  features={FEATS}")
def cv_auroc(feats):
    X = df[feats].fillna(-1.0).values; y = df["correct"].values; g = df["doc"].values
    oof = np.zeros(len(df))
    for tr, te in GroupKFold(5).split(X, y, g):
        m = GradientBoostingClassifier(random_state=0); m.fit(X[tr], y[tr]); oof[te] = m.predict_proba(X[te])[:, 1]
    return L.auroc(oof, df["correct"].values.astype(bool))
full = cv_auroc(FEATS)
print(f"\nFULL model (8 features) CV AUROC = {full:.3f}   (production pooled proba = 0.955)")
reconciled = full >= 0.90
out = {"full_auroc": round(full, 3), "reconciled_to_production": bool(reconciled), "drop_one_delta": {}}
if reconciled:
    print("RECONCILED -> drop-one ablation:")
    for c in FEATS:
        a = cv_auroc([x for x in FEATS if x != c]); d = full - a
        out["drop_one_delta"][c] = round(d, 3)
        print(f"  drop {c:20s} AUROC={a:.3f}  (Δ={d:+.3f})")
    ranked = sorted(out["drop_one_delta"].items(), key=lambda kv: -kv[1])
    out["most_important_by_dropone"] = [k for k, v in ranked[:4]]
    print("  most important (by drop-one):", out["most_important_by_dropone"])
else:
    print("NOT reconciled (my GBM != production RF+GBM ensemble) -> use production feature importances instead.")
json.dump(out, open(f"{os.path.dirname(__file__)}/../analysis/signal_dropone.json", "w"), indent=1)
print("saved -> analysis/signal_dropone.json")
