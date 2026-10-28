#!/usr/bin/env python3
"""VRDU realistic structured frontier. Replicates the finalized v3 exact correctness
(compute_vrdu_auroc_coverage.py: CLEAN GT, list-any-match via NTP matcher), score=wv_score,
deployed operating point = the stored `accept` decision. Pure python (NTP venv)."""
import json, re, sys, random
from pathlib import Path
NTP = "/Users/rajeshgupta/Git_Clones/NTP/NTP"; sys.path.insert(0, NTP)
import compute_roi
EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
EXP = EBV / "experiments"; V2 = EXP / "structured_ntp/vrdu"; RES = EXP / "results" / "vrdu_results"
CLEAN = json.loads((V2 / "gt_clean" / "ground_truth_vrdu_clean.json").read_text())
R = json.loads((RES / "extraction_results_vrdu.json").read_text()); EXk = next(iter(next(iter(R.values())).keys()))
def pof(d, f): return (R.get(d, {}).get(EXk, {}).get("extracted") or {}).get(f)
def cands(v):
    if v is None: return []
    xs = v if isinstance(v, list) else [v]
    return [str(x) for x in xs if x is not None and str(x).strip() != ""]
def nex(g, p, f):
    try: return bool(compute_roi.values_match_field_aware(g, p, f))
    except TypeError: return bool(compute_roi.values_match_field_aware(g, p))
def corr(d, f):  # exact, present population
    p = pof(d, f)
    if p is None: return None
    cg = cands(CLEAN.get(d, {}).get(f))
    if cg: return any(nex(c, str(p), f) for c in cg)
    return None   # GT-empty in present pop -> excluded
def auroc(pairs):
    pos = [s for s, c in pairs if c]; neg = [s for s, c in pairs if not c]
    if not pos or not neg: return None
    allp = sorted(pairs, key=lambda x: x[0]); r = [0.0]*len(allp); j = 0
    while j < len(allp):
        k = j
        while k+1 < len(allp) and allp[k+1][0] == allp[j][0]: k += 1
        avg = (j+k)/2+1
        for t in range(j, k+1): r[t] = avg
        j = k+1
    sr = sum(r[i] for i, (s, c) in enumerate(allp) if c)
    return (sr - len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))

SIGNER = {"signer_name", "signer_title"}
def load(exclude_sig=False):
    rows = []
    for l in open(V2 / "matrix/vrdu_v3_gt_exact/decisions.jsonl"):
        r = json.loads(l)
        if exclude_sig and r["field"] in SIGNER: continue
        c = corr(r["doc"], r["field"])
        if c is None: continue
        rows.append({"doc": r["doc"], "field": r["field"], "correct": c,
                     "accept": bool(r.get("accept")), "wv": r.get("wv_score")})
    return rows

def report(rows, label):
    errs = [x for x in rows if not x["correct"]]
    corrs = [x for x in rows if x["correct"]]
    au = auroc([(x["wv"], x["correct"]) for x in rows if x["wv"] is not None])
    au_e2e = auroc([(x["wv"] if x["wv"] is not None else 0.0, x["correct"]) for x in rows])  # PAPER headline
    caught = sum(1 for x in errs if not x["accept"])
    slip = sum(1 for x in errs if x["accept"])
    cw = [x["wv"] for x in corrs if x["wv"] is not None]; cw.sort()
    cut = cw[len(cw)//2] if cw else 1.0   # median correct wv
    frontier = sum(1 for x in errs if x["accept"] and x["wv"] is not None and x["wv"] >= cut)
    # bootstrap CI on frontier rate by doc
    docs = list({x["doc"] for x in rows}); bydoc = {}
    for x in rows: bydoc.setdefault(x["doc"], []).append(x)
    rng = random.Random(0); vals = []
    for _ in range(500):
        samp = [y for d in (rng.choice(docs) for _ in docs) for y in bydoc[d]]
        e = [y for y in samp if not y["correct"]]
        if not e: continue
        fr = sum(1 for y in e if y["accept"] and y["wv"] is not None and y["wv"] >= cut)
        vals.append(fr/len(e))
    vals.sort(); ci = (round(vals[int(.025*len(vals))], 3), round(vals[int(.975*len(vals))], 3)) if vals else (None, None)
    d = {"label": label, "n": len(rows), "errors": len(errs),
         "AUROC_end_to_end_PAPER": round(au_e2e, 4) if au_e2e else None,
         "AUROC": round(au, 4) if au else None,
         "caught_rate": round(caught/max(len(errs), 1), 3), "slip_rate": round(slip/max(len(errs), 1), 3),
         "FRONTIER_confidently_wrong": round(frontier/max(len(errs), 1), 3), "frontier_n": frontier,
         "frontier_CI": list(ci)}
    print(f"\n== VRDU {label} ==  n={d['n']} errors={d['errors']}  AUROC={d['AUROC']} (target "
          f"{'0.896' if not label.endswith('nosig') else '0.927'})")
    print(f"   caught={d['caught_rate']} slip={d['slip_rate']}  FRONTIER confidently-wrong={d['FRONTIER_confidently_wrong']} "
          f"(n={frontier}/{len(errs)}) CI={ci}")
    return d

out = {"all_fields": report(load(False), "all"),
       "excl_signature": report(load(True), "nosig")}
json.dump(out, open(Path(__file__).parent / "../analysis/vrdu_indirect.json", "w"), indent=1)
print("\nsaved -> analysis/vrdu_indirect.json")
