import json, sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import lib_frontier as L

U = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/unstructured_ntp"
DOMAINS = {
    "FCC":       f"{U}/realkie_fcc/decisions/fcc_decisions_clean.jsonl",
    "S1":        f"{U}/realkie_s1/decisions/realkie_s1_clean.jsonl",
    "Charities": f"{U}/realkie_charities/decisions/realkie_charities_clean.jsonl",
    "NDA":       f"{U}/realkie_nda/decisions/realkie_nda_clean.jsonl",
}
# Paper's Signal leg = SCALAR fields only (lineitem = tables leg). Fused score = `proba`.
CHAN = ["format_valid", "keyword_context", "source_context", "value_in_text",
        "label_value_distance", "cross_field_copy"]

def num(x):
    if x is True: return 1.0
    if x is False: return 0.0
    if x is None: return np.nan
    try: return float(x)
    except: return np.nan

def load(path):
    rows = []
    for ln in open(path):
        o = json.loads(ln)
        if o.get("field_type") != "scalar":   # SCALAR ONLY (paper Signal leg)
            continue
        sig = o.get("signals") or {}
        r = {"doc": o.get("doc"), "field": o.get("field"),
             "correct": bool(o.get("correct")),
             "accept": bool(o.get("accept_3t")),
             "fused": num(o.get("proba"))}        # proba reproduces paper AUROC
        for c in CHAN: r[c] = num(sig.get(c))
        rows.append(r)
    return pd.DataFrame(rows)

def orient(df, chans):
    d = {}
    for c in chans:
        a = L.auroc(df[c].values, df["correct"].values)
        if np.isnan(a): continue
        d[c] = "low" if a >= 0.5 else "high"
    return d

def analyze(df, label):
    chans = orient(df, CHAN)                      # 6 evidence channels
    oracle = dict(chans);
    # add the fused verifier as a detector (best use of the same evidence)
    fdir = "low" if L.auroc(df["fused"].values, df["correct"].values) >= 0.5 else "high"
    oracle_f = dict(chans); oracle_f["fused"] = fdir

    res = {"label": label, "n": int(len(df)), "n_err": int((~df["correct"]).sum()),
           "channel_dirs": chans}
    res["channel_auroc"] = {c: round(max(a, 1 - a), 3) for c in chans
                            for a in [L.auroc(df[c].values, df["correct"].values)]}
    res["fused_auroc"] = round(max(L.auroc(df["fused"].values, df["correct"].values),
                                   1 - L.auroc(df["fused"].values, df["correct"].values)), 3)
    # DEPLOYED operating point = binary accept decision (accept_3t); fused = proba
    rep = L.deployed_report(df, "fused", fused_dir=fdir, accept_col="accept", indist_pct=50)
    res["caught_rate"] = round(rep["caught_rate"], 3)
    res["slip_rate"] = round(rep["slip_rate"], 3)
    res["FRONTIER_confidently_wrong"] = round(rep["frontier_rate"], 3)
    res["frontier_n"] = rep["frontier_confidently_wrong"]
    res["complementarity"] = L.complementarity(df, chans, frr=0.05)
    res["placebo"] = L.placebo_frontier(df, chans, fused_col="fused", fused_dir=fdir, frr=0.05, n=200)
    cr = lambda s: L.deployed_report(s, "fused", fused_dir=fdir, accept_col="accept")["frontier_rate"]
    res["frontier_CI"] = [round(x, 3) for x in L.bootstrap_ci(df, cr, group="doc", n=500)]
    return res

out, frames = {}, {}
for name, path in DOMAINS.items():
    if not os.path.exists(path): print("MISSING", path); continue
    df = load(path); frames[name] = df
    out[name] = analyze(df, name)

paper = pd.concat([frames[k] for k in ("FCC", "S1", "Charities") if k in frames], ignore_index=True)
out["POOLED_paper"] = analyze(paper, "POOLED(FCC+S1+Charities)")

json.dump(out, open(f"{os.path.dirname(__file__)}/../analysis/signal_indirect.json", "w"), indent=1)
for k, r in out.items():
    print(f"\n==== {k}  n={r['n']} scalar fields, errors={r['n_err']} ====")
    print(f"  fused AUROC={r['fused_auroc']}  channels={r['channel_auroc']}")
    print(f"  DEPLOYED(accept_3t): caught={r['caught_rate']} slip={r['slip_rate']}")
    print(f"  *** FRONTIER confidently-wrong={r['FRONTIER_confidently_wrong']} (n={r['frontier_n']}/{r['n_err']}) CI={r['frontier_CI']}")
    print(f"  placebo: real={r['placebo']['real']:.3f} vs permuted={r['placebo']['placebo_mean']:.3f}±{r['placebo']['placebo_std']:.3f}")
    uq = {c: v['unique'] for c, v in r['complementarity'].items() if v['unique'] > 0}
    print(f"  unique channel capture: {uq}")
print("\nsaved -> analysis/signal_indirect.json")
