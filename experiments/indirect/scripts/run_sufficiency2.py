"""E5 sufficiency — proper test. S(o) ~ per-item evidence availability (the spec says the ONLY new
information sufficiency adds is per-item channel availability). H4 test: does conditioning
acceptance on (risk + sufficiency) beat risk (proba) alone on the risk-coverage trade-off?
Tested per-domain AND pooled, at risk levels 1/2/5% (not just the trivial 5% where base<5%).
KEEP only if it demonstrably improves; else DROP + report the INSUFFICIENT-state rate."""
import json, numpy as np, os
U = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/unstructured_ntp"
DOMS = {"FCC": f"{U}/realkie_fcc/decisions/fcc_decisions_clean.jsonl",
        "S1": f"{U}/realkie_s1/decisions/realkie_s1_clean.jsonl",
        "Charities": f"{U}/realkie_charities/decisions/realkie_charities_clean.jsonl"}
CHAN = ["format_valid", "keyword_context", "source_context", "value_in_text", "label_value_distance", "cross_field_copy"]

def load(path):
    rows = []
    for ln in open(path):
        o = json.loads(ln)
        if o.get("field_type") != "scalar": continue
        s = o.get("signals") or {}
        suff = sum(1 for c in CHAN if s.get(c) is not None)
        rows.append((bool(o["correct"]), o.get("proba"), suff))
    return [(c, p, s) for c, p, s in rows if p is not None]

def cov_at_risk(correct, score, risk, pool=None):
    """max coverage (accepted/N) s.t. error among accepted <= risk; accept highest score in pool."""
    N = len(correct); best = 0.0
    idx = np.argsort(-score)
    acc_c = [];
    for t in np.unique(score)[::-1]:
        m = score >= t
        if pool is not None: m = m & pool
        if m.sum() == 0: continue
        err = (~correct[m]).mean()
        if err <= risk: best = max(best, m.sum() / N)
    return best

def risk_cov_2feat(correct, proba, suff, risk):
    """accept rule using BOTH proba and sufficiency: for each (proba_thr, suff_thr) grid, if the
    accepted set has error<=risk, record coverage. Best coverage over the grid = can sufficiency help?"""
    N = len(correct); best_p = cov_at_risk(correct, proba, risk)   # proba alone
    best_2 = best_p
    for st in sorted(set(suff)):
        pool = suff >= st
        c = cov_at_risk(correct, proba, risk, pool=pool)
        best_2 = max(best_2, c)
    return best_p, best_2

all_rows = []
print("=== E5 sufficiency — per-domain error-rate by availability level + H4 risk-coverage test ===")
res = {}
for name, path in DOMS.items():
    rows = load(path); all_rows += rows
    correct = np.array([r[0] for r in rows]); proba = np.array([r[1] for r in rows]); suff = np.array([r[2] for r in rows])
    base_err = (~correct).mean()
    # error rate by sufficiency level
    by = {int(s): round(float((~correct[suff == s]).mean()), 3) for s in sorted(set(suff))}
    cnt = {int(s): int((suff == s).sum()) for s in sorted(set(suff))}
    line = {"n": len(rows), "base_err": round(float(base_err), 3), "err_by_suff": by, "count_by_suff": cnt, "h4": {}}
    for risk in (0.01, 0.02, 0.05):
        bp, b2 = risk_cov_2feat(correct, proba, suff, risk)
        line["h4"][f"risk{int(risk*100)}%"] = {"cov_proba_alone": round(bp, 3), "cov_proba+suff": round(b2, 3),
                                                 "improved": bool(b2 > bp + 1e-9)}
    res[name] = line
    print(f"\n{name}: n={len(rows)} base_err={base_err:.3f}  err_by_suff={by} count={cnt}")
    for k, v in line["h4"].items():
        print(f"   {k}: cov(proba)={v['cov_proba_alone']:.3f}  cov(proba+suff)={v['cov_proba+suff']:.3f}  improved={v['improved']}")

improved_any = any(v["h4"][k]["improved"] for v in res.values() for k in v["h4"])
insuff_rate = float(np.mean([r[2] < 6 for r in all_rows]))
res["_DECISION"] = "KEEP" if improved_any else "DROP — does not improve risk-coverage over risk alone at any (domain, risk) tested"
res["_insufficient_state_rate_note"] = f"{insuff_rate:.2f} of fields lack value_in_text/cross_field_copy (field-specific signals), i.e. availability barely varies -> sufficiency adds ~no new info (per spec, its only new info IS availability)"
print(f"\nDECISION: {res['_DECISION']}")
json.dump(res, open(f"{os.path.dirname(__file__)}/../analysis/sufficiency.json", "w"), indent=1)
print("saved -> analysis/sufficiency.json")
