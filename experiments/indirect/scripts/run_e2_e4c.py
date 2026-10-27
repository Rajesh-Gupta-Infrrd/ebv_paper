"""E2 (channel ablation: drop-one AUROC) + E4c (oracle decomposition) for Signal + ParseBench.
Signal ablation uses a fresh GBM on the 6 evidence channels (clearly an ablation model, not the
production 9-feature model) with doc-grouped CV; it measures each channel's marginal contribution."""
import json, sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import lib_frontier as L
U = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/unstructured_ntp"
SIG_FILES = {"FCC": f"{U}/realkie_fcc/decisions/fcc_decisions_clean.jsonl",
             "S1": f"{U}/realkie_s1/decisions/realkie_s1_clean.jsonl",
             "Charities": f"{U}/realkie_charities/decisions/realkie_charities_clean.jsonl"}
CHAN = ["format_valid", "keyword_context", "source_context", "value_in_text", "label_value_distance", "cross_field_copy"]

def num(x):
    if x is True: return 1.0
    if x is False: return 0.0
    if x is None: return np.nan
    try: return float(x)
    except: return np.nan

def load_signal():
    rows = []
    for name, p in SIG_FILES.items():
        for ln in open(p):
            o = json.loads(ln)
            if o.get("field_type") != "scalar": continue
            s = o.get("signals") or {}
            r = {"doc": o["doc"], "correct": bool(o["correct"]), "accept": bool(o.get("accept_3t")),
                 "fused": num(o.get("proba"))}
            for c in CHAN: r[c] = num(s.get(c))
            rows.append(r)
    return pd.DataFrame(rows)

sig = load_signal()
# NOTE: a fresh-GBM drop-one ablation is NOT faithful here — the 6 content signals are near-constant
# (format_valid=0.8 for 98.6% of fields) and the production model's power comes from the full
# 9-feature set incl. empty-prior features. Per-channel contribution is reported via unique-capture
# (run_signal complementarity) instead. A faithful E2 needs production retraining (deferred).

# E4c oracle decomposition on Signal (pooled) + ParseBench
chans = {}
for c in CHAN:
    a = L.auroc(sig[c].values, sig["correct"].values)
    if not np.isnan(a): chans[c] = "low" if a >= 0.5 else "high"
dec = L.oracle_decompose(sig, chans, "fused", "low", "accept", frr=0.05)
print(f"\n=== E4c oracle decomposition — Signal pooled (errors={dec['n_err']}) ===")
print(f"  fusion caught {dec['fusion_caught_rate']:.3f} | observable-by-single-channel {dec['observable_rate']:.3f}")
print(f"  obs&caught={dec['obs_and_caught']}  obs-but-missed={dec['obs_but_missed']}  "
      f"fusion-only-caught={dec['fusiononly_caught']}  TRUE-frontier={dec['true_frontier_n']} ({dec['true_frontier_rate']:.3f})")

# ParseBench structural vs witness
pb = json.load(open(f"{os.path.dirname(__file__)}/../analysis/parsebench_indirect.json"))
vision = {0:1,1:1,2:1,3:1,4:1,5:1,6:1,7:1,8:1,9:1,10:1,11:1,12:0,13:1,14:1,15:1,16:1,17:1,18:1,19:1,20:1,21:1,22:1,
 23:0,24:0,25:1,26:1,27:1,28:1,29:0,30:1,32:1,33:1,34:1,35:0,36:1,37:1,38:1,39:1,40:1,41:1,42:1,43:1,44:1,45:1,46:1,
 47:1,48:1,49:1,50:1,51:0,52:1,53:1,54:1,55:1,56:1,57:1,58:1,59:1}
sg = {r["i"]: r for r in json.load(open(f"{os.path.dirname(__file__)}/../analysis/pb_signals.json"))}
prows = []
for i, v in vision.items():
    r = sg.get(i)
    if not r or r.get("trust") is None: continue
    s = r.get("signals") or {}
    def sc(n):
        d = s.get(n); return float(d["score"]) if isinstance(d, dict) and isinstance(d.get("score"), (int, float)) else np.nan
    prows.append({"doc": i, "correct": bool(v), "accept": float(r["trust"]) >= 85, "fused": float(r["trust"]),
                  "witness": sc("text_conservation"),
                  "structural": np.nanmin([sc("geometry"), sc("structural"), sc("reading_order"), sc("token_shape")])})
pdf = pd.DataFrame(prows)
print(f"\n=== E2 tables — witness-only vs structural-only (ParseBench, {int((~pdf.correct).sum())} BAD) ===")
for fam in ["witness", "structural"]:
    a = L.auroc(pdf[fam].values, pdf.correct.values)
    print(f"  {fam:12s} AUROC(vs vision)={max(a,1-a):.3f}")
pchans = {}
for c in ["witness", "structural"]:
    a = L.auroc(pdf[c].values, pdf.correct.values)
    if not np.isnan(a): pchans[c] = "low" if a >= 0.5 else "high"
pdec = L.oracle_decompose(pdf, pchans, "fused", "low", "accept", frr=0.05)
print(f"  oracle: observable-by-channel {pdec['observable_rate']:.2f}  fusion-caught {pdec['fusion_caught_rate']:.2f}  true-frontier {pdec['true_frontier_n']}")

out = {"E2_signal_ablation": "not-faithful (content signals near-constant; needs production retrain) — use complementarity",
       "E4c_signal": dec, "E4c_parsebench": pdec,
       "E2_tables_family_auroc": {f: round(max(L.auroc(pdf[f].values, pdf.correct.values),
                                               1 - L.auroc(pdf[f].values, pdf.correct.values)), 3) for f in ["witness", "structural"]}}
json.dump(out, open(f"{os.path.dirname(__file__)}/../analysis/e2_e4c.json", "w"), indent=1)
print("\nsaved -> analysis/e2_e4c.json")
