"""Analyze RD per-channel signals (from run_rd_signals.py, current scorer) to get the RELIABLE
structural-only vs witness-only discrimination on 287 clear cases (vs ParseBench's n=6).
Reconciliation gate: AUROC(trust_new, gt) must be close to the paper's RD 0.872; if so, the
current scorer is consistent enough for the structural-vs-witness RELATIVE comparison."""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import lib_frontier as L
d = json.load(open(f"{os.path.dirname(__file__)}/../analysis/rd_signals.json"))
def sc(r, name):
    s = (r.get("signals") or {}).get(name)
    return float(s["score"]) if isinstance(s, dict) and isinstance(s.get("score"), (int, float)) else np.nan
import numpy as np
correct = np.array([r["gt"] == "GOOD" for r in d])
trust = np.array([r["trust_new"] if isinstance(r["trust_new"], (int, float)) else np.nan for r in d])
chans = {c: np.array([sc(r, c) for r in d]) for c in ["geometry", "structural", "text_conservation", "crop"]}
print(f"RD re-scored clear cases: {len(d)}  GOOD={int(correct.sum())} BAD={int((~correct).sum())}")
au_trust = L.auroc(trust, correct)
print(f"RECONCILE GATE: AUROC(current trust, gt) = {au_trust:.3f}  (paper RD 0.872; close => scorer consistent)")
print("\nper-channel AUROC vs vision GOOD/BAD (the without-witness question):")
res = {"n": len(d), "good": int(correct.sum()), "bad": int((~correct).sum()),
       "reconcile_trust_auroc": round(au_trust, 3), "paper_rd_auroc": 0.872, "channel_auroc": {}}
for c, v in chans.items():
    a = L.auroc(v, correct); nn = np.isnan(v).mean()
    disc = max(a, 1 - a) if a == a else float("nan")
    res["channel_auroc"][c] = {"auroc": round(disc, 3), "nan_frac": round(float(nn), 2)}
    print(f"  {c:18s} AUROC={disc:.3f}  (nan {nn*100:.0f}%)")
struct = res["channel_auroc"]["structural"]["auroc"]; wit = res["channel_auroc"]["text_conservation"]["auroc"]
res["structural_only_auroc"] = struct
res["witness_only_auroc"] = wit
res["verdict"] = ("witness clearly stronger" if wit - struct > 0.08 else
                  "comparable" if abs(wit - struct) <= 0.08 else "structural stronger")
print(f"\nSTRUCTURAL-only AUROC = {struct}   WITNESS-only AUROC = {wit}   -> {res['verdict']}")
json.dump(res, open(f"{os.path.dirname(__file__)}/../analysis/rd_structural.json", "w"), indent=1)
print("saved -> analysis/rd_structural.json")
