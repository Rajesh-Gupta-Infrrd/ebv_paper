import json, sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import lib_frontier as L

# vision labels (same as pb_vision_auroc.py): 1=GOOD 0=BAD ; idx31 excluded (no trust)
vision = {0:1,1:1,2:1,3:1,4:1,5:1,6:1,7:1,8:1,9:1,10:1,11:1,12:0,13:1,14:1,15:1,16:1,17:1,18:1,19:1,
 20:1,21:1,22:1,23:0,24:0,25:1,26:1,27:1,28:1,29:0,30:1,32:1,33:1,34:1,35:0,36:1,37:1,38:1,39:1,40:1,
 41:1,42:1,43:1,44:1,45:1,46:1,47:1,48:1,49:1,50:1,51:0,52:1,53:1,54:1,55:1,56:1,57:1,58:1,59:1}
sig = {r["i"]: r for r in json.load(open(f"{os.path.dirname(__file__)}/../analysis/pb_signals.json"))}
STRUCT = ["geometry", "structural", "reading_order", "token_shape"]   # HTML-internal priors
WIT = "text_conservation"                                            # independent OCR witness

rows = []
for i, v in vision.items():
    r = sig.get(i)
    if r is None or r.get("trust") is None: continue
    s = r.get("signals") or {}
    def sc(name):
        d = s.get(name);
        return float(d["score"]) if isinstance(d, dict) and isinstance(d.get("score"), (int, float)) else np.nan
    row = {"i": i, "doc": i, "correct": bool(v), "fused": float(r["trust"]),
           "witness": sc(WIT)}
    for c in STRUCT: row[c] = sc(c)
    rows.append(row)
df = pd.DataFrame(rows)
df["accept"] = df.fused >= 85
print(f"ParseBench: n={len(df)}  GOOD={int(df.correct.sum())}  BAD={int((~df.correct).sum())}")
print(f"  AUROC(trust vs vision)={L.auroc(df.fused.values, df.correct.values):.3f}")

rep = L.deployed_report(df, "fused", fused_dir="low", accept_col="accept", indist_pct=50)
print(f"  DEPLOYED(trust>=85): caught={rep['caught_rate']:.3f} ({rep['caught']}/{rep['n_err']})  slip={rep['slip_rate']:.3f}")
print(f"  FRONTIER confidently-wrong={rep['frontier_rate']:.3f} (n={rep['frontier_confidently_wrong']}/{rep['n_err']})")

# structural-vs-witness complementarity on the BAD tables
chans = {}
for c in ["witness"] + STRUCT:
    a = L.auroc(df[c].values, df.correct.values)
    if not np.isnan(a): chans[c] = "low" if a >= 0.5 else "high"
comp = L.complementarity(df, chans, frr=0.05)
print("  per-channel capture of BAD (structural vs witness):")
for c, vv in comp.items():
    fam = "WITNESS" if c == "witness" else "structural"
    print(f"    {c:16s}[{fam}] covers={vv['covers']} unique={vv['unique']}")
# which family flags each BAD
print("  per-BAD-table channel scores:")
for _, r in df[~df.correct].iterrows():
    print(f"    idx{int(r.i):2d} trust={r.fused:5.1f} witness={r.witness if r.witness==r.witness else 'NA'} "
          f"geom={r.geometry if r.geometry==r.geometry else 'NA'} struct={r.structural if r.structural==r.structural else 'NA'}")

out = {"n": len(df), "good": int(df.correct.sum()), "bad": int((~df.correct).sum()),
       "auroc_trust_vision": round(L.auroc(df.fused.values, df.correct.values), 3),
       "caught_rate": round(rep["caught_rate"], 3), "slip_rate": round(rep["slip_rate"], 3),
       "FRONTIER_confidently_wrong": round(rep["frontier_rate"], 3),
       "frontier_n": rep["frontier_confidently_wrong"],
       "complementarity_struct_vs_witness": comp,
       "note": "ParseBench vision labels (6 BAD); structural=geometry/structural/reading_order/token_shape, witness=text_conservation"}
json.dump(out, open(f"{os.path.dirname(__file__)}/../analysis/parsebench_indirect.json", "w"), indent=1)
print("\nsaved -> analysis/parsebench_indirect.json")
