import json, re, sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import lib_frontier as L

EXP = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments"
V2 = f"{EXP}/structured_ntp/fatura"
RES = f"{EXP}/results/fatura_results"
R = json.load(open(f"{RES}/extraction_results_fatura.json"))
GT = json.load(open(f"{RES}/ground_truth_fatura.json"))
EXk = next(iter(next(iter(R.values())).keys()))
AL = re.compile(r"[^a-z0-9]+")
def pof(d, f): return (R.get(d, {}).get(EXk, {}).get("extracted") or {}).get(f)
def norm(x): return AL.sub("", str(x).lower()) if x is not None else ""
def contain(p, g):
    p, g = norm(p), norm(g)
    if not p or not g: return False
    return (p == g) if len(p) < 2 else (p in g or g in p)
def gt_empty(g): return g is None or str(g).strip().lower() in ("", "none")
def clean_label(doc, field, exact_correct):
    # A-handled (keepB), identical to recompute_fatura_clean.py
    if exact_correct: return True
    p = pof(doc, field); g = GT.get(doc, {}).get(field)
    if contain(p, g) and not gt_empty(g): return True      # A -> correct
    return False                                            # B (GT-empty) or C -> error

rows = []
for l in open(f"{V2}/task3b_gt_endtoend_exact/decisions.jsonl"):
    r = json.loads(l); ec = r.get("correct")
    if ec is None: continue
    p = pof(r["doc"], r["field"])
    if p is None or str(p).strip() == "": continue          # present-field (same restriction)
    def fl(k):
        v = r.get(k)
        return float(v) if isinstance(v, (int, float)) and v == v else np.nan
    rows.append({"doc": r["doc"], "field": r["field"],
                 "correct": clean_label(r["doc"], r["field"], bool(ec)),
                 "accept": bool(r.get("accept")),
                 "located": 1.0 if r.get("located") else 0.0,
                 "overlap": fl("overlap"), "center": fl("center"), "iou": fl("iou"),
                 "fused": fl("wv_score")})
df = pd.DataFrame(rows)
# wv_score null (not located) = strongest contradiction -> fill 0 for the fused score only
df["fused_filled"] = df["fused"].fillna(0.0)
print(f"FATURA present fields: {len(df)}  correct={int(df.correct.sum())}  errors={int((~df.correct).sum())}")

# RECONCILIATION: AUROC(wv_score, A-handled) on LOCATED (non-None) scores = finalized 0.994
au = L.auroc(df["fused"].values, df["correct"].values)   # L.auroc drops NaN -> excludes not-located
print(f"RECONCILE AUROC(wv_score, A-handled, located-only) = {au:.4f}  (target 0.994)")
print(f"  error wv max={np.nanmax(df[~df.correct]['fused'].values):.3f}  correct wv median={np.nanmedian(df[df.correct]['fused'].values):.3f}  "
      f"-> separation near-perfect; errors unscored(not-located)={int(df[~df.correct]['fused'].isna().sum())}/{int((~df.correct).sum())}")
# PAPER HEADLINE: end-to-end AUROC over ALL present fields (unscored = lowest trust)
au_e2e = L.auroc(df["fused_filled"].values, df["correct"].values)
print(f"END-TO-END AUROC (all present, unscored=lowest trust; PAPER headline) = {au_e2e:.4f}  (target 0.95)")

CHAN = {"located": "low", "overlap": "low", "iou": "low", "center": "high"}  # dirs auto-checked below
# auto-orient channels
chans = {}
for c in CHAN:
    a = L.auroc(df[c].values, df["correct"].values)
    if not np.isnan(a): chans[c] = "low" if a >= 0.5 else "high"

fdir = "low"  # low wv_score = contradiction
rep = L.deployed_report(df, "fused_filled", fused_dir=fdir, accept_col="accept", indist_pct=50)
print(f"\nDEPLOYED (ROI accept decision):  caught={rep['caught_rate']:.3f} ({rep['caught']}/{rep['n_err']})  "
      f"slip-through={rep['slip_rate']:.3f} ({rep['slip_through']})")
print(f"  FRONTIER (confidently-wrong: accepted error wv>=median correct)={rep['frontier_rate']:.3f} "
      f"(n={rep['frontier_confidently_wrong']}/{rep['n_err']})  cut={rep['indist_cut']}")
cr = lambda s: L.deployed_report(s, "fused_filled", fused_dir=fdir, accept_col="accept")["frontier_rate"]
ci = L.bootstrap_ci(df, cr, group="doc", n=500)
print(f"  frontier CI: {tuple(round(x,3) for x in ci)}")
comp = L.complementarity(df, chans, frr=0.05)
print(f"  spatial-channel complementarity (unique capture): "
      f"{ {c: v['unique'] for c, v in comp.items() if v['unique']>0} }")

out = {"n": len(df), "correct": int(df.correct.sum()), "errors": int((~df.correct).sum()),
       "operating_point": "ROI accept decision (GT-ROI exact calib ON, A-handled keepB labels)",
       "auroc_end_to_end_PAPER": round(au_e2e, 4),
       "auroc_located_only": round(au, 4),
       "caught_rate": round(rep["caught_rate"], 3), "slip_rate": round(rep["slip_rate"], 3),
       "FRONTIER_confidently_wrong": round(rep["frontier_rate"], 3),
       "frontier_n": rep["frontier_confidently_wrong"], "frontier_CI": [round(x, 3) for x in ci],
       "channel_complementarity": comp,
       "note": "FATURA finalized v3 (task3b, wv_score, exact + A-handled keepB). B=GT-empty spurious kept as error."}
json.dump(out, open(f"{os.path.dirname(__file__)}/../analysis/roi_indirect.json", "w"), indent=1)
print("\nsaved -> analysis/roi_indirect.json")
