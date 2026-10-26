"""E5 sufficiency: does conditioning acceptance on evidence-sufficiency (how many channels are
applicable for a field) improve the risk-coverage trade-off over risk (proba) alone? Keep only if
it does (H4), else drop and report the INSUFFICIENT-state rate as an honesty number."""
import json, numpy as np, os
U = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/unstructured_ntp"
FILES = [f"{U}/realkie_fcc/decisions/fcc_decisions_clean.jsonl",
         f"{U}/realkie_s1/decisions/realkie_s1_clean.jsonl",
         f"{U}/realkie_charities/decisions/realkie_charities_clean.jsonl"]
CHAN = ["format_valid", "keyword_context", "source_context", "value_in_text", "label_value_distance", "cross_field_copy"]
def applicable(v):  # a channel is "applicable" if it gives a non-null, non-neutral reading
    return v is not None
rows = []
for p in FILES:
    for ln in open(p):
        o = json.loads(ln)
        if o.get("field_type") != "scalar": continue
        s = o.get("signals") or {}
        suff = sum(1 for c in CHAN if applicable(s.get(c)))   # 0..6 applicable channels
        rows.append({"correct": bool(o["correct"]), "proba": o.get("proba"), "suff": suff})
rows = [r for r in rows if r["proba"] is not None]
n = len(rows)
proba = np.array([r["proba"] for r in rows]); correct = np.array([r["correct"] for r in rows]); suff = np.array([r["suff"] for r in rows])
print(f"n={n}  sufficiency distribution (applicable-channel count):",
      {int(k): int((suff == k).sum()) for k in np.unique(suff)})

def cov_at_risk(mask_accept_pool, risk=0.05):
    """max coverage (accepted/all n) s.t. error among accepted <= risk, accepting highest-proba
    inside the allowed pool (others -> review)."""
    best = 0.0
    for t in np.linspace(0, 1, 101):
        acc = mask_accept_pool & (proba >= t)
        if acc.sum() == 0: continue
        err = (~correct[acc]).mean()
        if err <= risk:
            best = max(best, acc.sum() / n)
    return best

allpool = np.ones(n, bool)
base = cov_at_risk(allpool)
print(f"\ncoverage@5%risk, PROBA alone = {base:.3f}")
best_s = None
for s_thr in range(0, 7):
    pool = suff >= s_thr
    cov = cov_at_risk(pool)
    print(f"  require sufficiency>={s_thr} ({pool.mean()*100:.0f}% of fields eligible): coverage@5%risk = {cov:.3f}")
    if best_s is None or cov > best_s[1]: best_s = (s_thr, cov)
improved = best_s[1] > base + 1e-9
# INSUFFICIENT-state rate: fields with < full sufficiency (honesty number)
insuff_rate = float((suff < 6).mean())
out = {"n": n, "coverage_proba_alone": round(base, 3),
       "best_sufficiency_gate": {"threshold": best_s[0], "coverage": round(best_s[1], 3)},
       "sufficiency_improves_over_risk_alone": bool(improved),
       "DECISION": "KEEP" if improved else "DROP (does not beat risk alone; report INSUFFICIENT-rate instead)",
       "insufficient_state_rate": round(insuff_rate, 3)}
print(f"\nsufficiency improves over risk alone? {improved}  -> {out['DECISION']}")
print(f"INSUFFICIENT-state rate (fields without all 6 channels applicable) = {insuff_rate:.3f}")
json.dump(out, open(f"{os.path.dirname(__file__)}/../analysis/sufficiency.json", "w"), indent=1)
print("saved -> analysis/sufficiency.json")
