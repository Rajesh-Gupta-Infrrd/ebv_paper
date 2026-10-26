import json, sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import lib_frontier as L

RD = "/Users/rajeshgupta/Projects/DocAI/eval/table_extraction/rdbench/table_trust_eval"
d = json.load(open(f"{RD}/review_data.json"))
# exclude either-or (header/title drop, cls==HDR); clear cases only
rows = []
for r in d:
    if r.get("cls") == "HDR":
        continue
    rows.append({"case": r["case_id"], "correct": r["gt"] == "GOOD",
                 "family": r["defect"], "fused": float(r["trust"]), "cls": r["cls"]})
df = pd.DataFrame(rows)
df["doc"] = df["case"]
print(f"RD clear cases: {len(df)}  GOOD={int(df.correct.sum())}  BAD={int((~df.correct).sum())}")
print("families:", dict(df[~df.correct].family.value_counts()))

fdir = "low"  # low trust = contradiction
# DEPLOYED operating point = product threshold trust>=85 (ACCEPT iff trust>=85)
df["accept"] = df.fused >= 85
rep = L.deployed_report(df, "fused", fused_dir=fdir, accept_col="accept", indist_pct=50)
print(f"\nDEPLOYED (trust>=85):  caught={rep['caught_rate']:.3f} ({rep['caught']}/{rep['n_err']})  "
      f"slip-through={rep['slip_rate']:.3f} ({rep['slip_through']})")
print(f"  FRONTIER (confidently-wrong: accepted error scored >= median GOOD trust)={rep['frontier_rate']:.3f} "
      f"(n={rep['frontier_confidently_wrong']}/{rep['n_err']})  cut={rep['indist_cut']}")
cr = lambda s: L.deployed_report(s.assign(accept=s.fused >= 85), "fused", "low", accept_col="accept")["frontier_rate"]
ci = L.bootstrap_ci(df, cr, group="doc", n=1000)
print(f"  frontier CI: {tuple(round(x,3) for x in ci)}")
print(f"  fused AUROC(trust vs good)={L.auroc(df.fused.values, df.correct.values):.3f}")
# placebo on catch (shuffle trust -> catch must collapse to ~false-accept base)
pb = L.placebo_frontier(df, {}, fused_col="fused", fused_dir=fdir, frr=0.05, n=300)
print(f"  placebo (detectable@5%FRR): real={pb['real']:.3f} vs permuted={pb['placebo_mean']:.3f}±{pb['placebo_std']:.3f}")
fr = {"fusion_capture": rep["caught_rate"], "fusion_false_flag": None, "undetectable": rep["slip_rate"],
      "undetectable_n": rep["slip_through"]}  # back-compat for the json dump below

# per-family detectability map: catch rate @ DEPLOYED threshold (trust>=85) + AUROC within family-vs-GOOD
good = df[df.correct]
thr = 85.0
print(f"\nDETECTABILITY MAP (catch rate @ deployed trust>=85):")
fam_out = {}
for fam in df[~df.correct].family.unique():
    sub = df[df.family == fam]
    cap = float((sub.fused.values < thr).mean())   # fraction caught (rejected) at deployed threshold
    au = L.auroc(pd.concat([good, sub]).fused.values, pd.concat([good, sub]).correct.values)
    fam_out[fam] = {"n": int(len(sub)), "catch@deployed": round(cap, 3), "auroc_vs_good": round(au, 3)}
    print(f"  {fam:22s} n={len(sub):3d}  catch@deployed={cap:.3f}  AUROC={au:.3f}")

out = {"n": len(df), "good": int(df.correct.sum()), "bad": int((~df.correct).sum()),
       "operating_point": "deployed trust>=85",
       "fused_auroc": round(L.auroc(df.fused.values, df.correct.values), 3),
       "caught_rate": round(rep["caught_rate"], 3), "slip_rate": round(rep["slip_rate"], 3),
       "FRONTIER_confidently_wrong": round(rep["frontier_rate"], 3),
       "frontier_n": rep["frontier_confidently_wrong"], "frontier_CI": [round(x, 3) for x in ci],
       "placebo": pb, "detectability_map": fam_out,
       "note": "deployed-threshold view; structural-vs-witness per-channel complementarity pending scorer re-emit (pb_signals)"}
json.dump(out, open(f"{os.path.dirname(__file__)}/../analysis/rd_indirect.json", "w"), indent=1)
print("\nsaved -> analysis/rd_indirect.json")
