#!/usr/bin/env python3
"""VRDU per-family map (ROI/structured, REAL docs — frontier 2.6%, so informative unlike FATURA).
Families from pred/GT (no source text available for VRDU → no source-absent class). NTP venv."""
import json, re, sys
from pathlib import Path
NTP = "/Users/rajeshgupta/Git_Clones/NTP/NTP"; sys.path.insert(0, NTP); import compute_roi
EXP = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments"
V2 = f"{EXP}/structured_ntp/vrdu"; RES = f"{EXP}/results/vrdu_results"
CLEAN = json.load(open(f"{V2}/gt_clean/ground_truth_vrdu_clean.json"))
R = json.load(open(f"{RES}/extraction_results_vrdu.json")); EXk = next(iter(next(iter(R.values())).keys()))
AL = re.compile(r"[^a-z0-9]+"); norm = lambda x: AL.sub("", str(x).lower()) if x is not None else ""
def pof(d, f): return (R.get(d, {}).get(EXk, {}).get("extracted") or {}).get(f)
def cands(v): return [str(x) for x in (v if isinstance(v, list) else [v]) if x is not None and str(x).strip() != ""] if v is not None else []
def nex(g, p, f):
    try: return bool(compute_roi.values_match_field_aware(g, p, f))
    except TypeError: return bool(compute_roi.values_match_field_aware(g, p))
def correct(d, f):
    p = pof(d, f)
    if p is None: return None
    cg = cands(CLEAN.get(d, {}).get(f))
    return (any(nex(c, str(p), f) for c in cg)) if cg else None
def family(d, f, pred):
    p = norm(pred)
    if p == "": return "missing"
    # cross-field copy: pred == another field's clean-GT value in same doc
    for of, v in CLEAN.get(d, {}).items():
        if of == f: continue
        for c in cands(v):
            if len(norm(c)) > 3 and norm(c) == p: return "cross_field_copy"
    return "wrong_value"

from collections import Counter
# iterate the SAME scored set as the finalized VRDU analysis (the decisions file) -> 544 errors
rows = []
for l in open(f"{V2}/matrix/vrdu_v3_gt_exact/decisions.jsonl"):
    r = json.loads(l); d, f = r["doc"], r["field"]
    c = correct(d, f)
    if c is None or c: continue   # present-field errors only (matches run_vrdu)
    rows.append({"family": family(d, f, pof(d, f)), "caught": not bool(r.get("accept"))})
famc = Counter(r["family"] for r in rows)
print(f"VRDU errors={len(rows)}  family dist={dict(famc)}")
out = {"n_errors": len(rows), "family_distribution": dict(famc), "detectability_map": {}}
for fam in famc:
    sub = [r for r in rows if r["family"] == fam]; cr = sum(1 for r in sub if r["caught"]) / len(sub)
    out["detectability_map"][fam] = {"n": len(sub), "caught_at_deployed": round(cr, 3)}
    print(f"  {fam:18s} n={len(sub):4d}  caught@deployed={cr:.3f}")
json.dump(out, open(f"{Path(__file__).parent}/../analysis/vrdu_atlas.json", "w"), indent=1)
print("saved -> analysis/vrdu_atlas.json")
