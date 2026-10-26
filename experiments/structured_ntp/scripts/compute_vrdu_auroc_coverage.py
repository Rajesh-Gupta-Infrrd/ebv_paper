#!/usr/bin/env python3
"""Compute AUROC + coverage@fixed-risk for VRDU (present-field), the SAME metrics Jin et al.
(2609.20110) report, so VRDU is expressed on the competitor's axes. Reuses the exact
correctness logic + paths from doc_structured_vrdu.py (list-GT aware). Writes the numbers
into paper/structured_vrdu_metrics.json under key 'auroc_coverage_present' (leaves existing
keys untouched) and prints a table. No dataset re-download, no model call."""
import json, re, sys
from pathlib import Path
NTP = "/Users/rajeshgupta/Git_Clones/NTP/NTP"; sys.path.insert(0, NTP)
import compute_roi  # noqa
EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
EXP = EBV / "experiments"; V2 = EXP / "structured_ntp/vrdu"; RES = EXP / "results" / "vrdu_results"
AL = re.compile(r"[^a-z0-9]+")
RAW = json.loads((RES / "ground_truth_vrdu.json").read_text())
CLEAN = json.loads((V2 / "gt_clean" / "ground_truth_vrdu_clean.json").read_text())
R = json.loads((RES / "extraction_results_vrdu.json").read_text()); EXk = next(iter(next(iter(R.values())).keys()))


def pof(d, f): return (R.get(d, {}).get(EXk, {}).get("extracted") or {}).get(f)


def cands(v):
    if v is None: return []
    xs = v if isinstance(v, list) else [v]
    return [str(x) for x in xs if x is not None and str(x).strip() != ""]


def contain(p, g):
    p, g = AL.sub("", (p or "").lower()), AL.sub("", (g or "").lower())
    return (p == g if len(p) < 2 else (p in g or g in p)) if p and g else False


def nex(g, p, f):
    try: return bool(compute_roi.values_match_field_aware(g, p, f))
    except TypeError: return bool(compute_roi.values_match_field_aware(g, p))


def corr(d, f, mode, pop):
    p = pof(d, f)
    if p is None: return None
    if mode == "exact":
        cg = cands(CLEAN.get(d, {}).get(f))
        if cg: return any(nex(c, str(p), f) for c in cg)
        return False if pop == "full" else None
    rg = cands(RAW.get(d, {}).get(f))
    if rg: return any(contain(str(p), c) for c in rg)
    return False if pop == "full" else None


def auroc(pairs):  # pairs=(score, correct) with score not None
    pos = [s for s, c in pairs if c]; neg = [s for s, c in pairs if not c]
    if not pos or not neg: return None
    allp = sorted(pairs, key=lambda x: x[0])
    r = [0.0] * len(allp); j = 0
    while j < len(allp):
        k = j
        while k + 1 < len(allp) and allp[k + 1][0] == allp[j][0]: k += 1
        avg = (j + k) / 2 + 1
        for t in range(j, k + 1): r[t] = avg
        j = k + 1
    sr = sum(r[idx] for idx, (s, c) in enumerate(allp) if c)
    npos, nneg = len(pos), len(neg)
    return (sr - npos * (npos + 1) / 2) / (npos * nneg)


def cov_at_risk(rows, targets=(0.05, 0.10, 0.20)):
    # rows=(score_or_None, correct); accepted = score>=t (unlocated never accepted). denom = all rows.
    n = len(rows); scored = [(s, c) for s, c in rows if s is not None]; out = {}
    for tgt in targets:
        best = 0.0
        for i in range(101):
            t = i / 100; acc = [c for s, c in scored if s >= t]
            if not acc: continue
            risk = sum(1 for c in acc if not c) / len(acc)
            if risk <= tgt: best = max(best, len(acc) / n)
        out[tgt] = best
    return out


CELLS = {("v1", "exact"): "matrix/vrdu_v1_pred_nocalib/decisions.jsonl",
         ("v1", "containment"): "matrix/vrdu_v1_pred_nocalib/decisions.jsonl",
         ("v2", "exact"): "matrix/vrdu_v2_pred_exact/decisions.jsonl",
         ("v2", "containment"): "matrix/vrdu_v2_pred_contain/decisions.jsonl",
         ("v3", "exact"): "matrix/vrdu_v3_gt_exact/decisions.jsonl",
         ("v3", "containment"): "matrix/vrdu_v3_gt_contain/decisions.jsonl",
         ("v4", "exact"): "matrix/vrdu_v4_gt_nocalib/decisions.jsonl",
         ("v4", "containment"): "matrix/vrdu_v4_gt_nocalib/decisions.jsonl"}
CFG = {"v1": "pred-ROI, calib OFF", "v2": "pred-ROI, calib ON",
       "v3": "GT-ROI, calib ON (prod)", "v4": "GT-ROI, calib OFF"}


def one(path, mode, pop="present"):
    rows = []
    for l in open(V2 / path):
        r = json.loads(l); c = corr(r["doc"], r["field"], mode, pop)
        if c is None: continue
        rows.append((r.get("wv_score"), c))
    a = auroc([(s, c) for s, c in rows if s is not None])
    cov = cov_at_risk(rows)
    nscored = sum(1 for s, _ in rows if s is not None)
    return {"n": len(rows), "n_scored": nscored, "AUROC": round(a, 4) if a is not None else None,
            "cov@5%": round(cov[0.05], 4), "cov@10%": round(cov[0.10], 4), "cov@20%": round(cov[0.20], 4)}


def main():
    data = {}
    print(f"{'ver':24} {'corr':12} {'n':>5} {'scored':>7} {'AUROC':>7}  cov@5/10/20%")
    for v in ["v1", "v2", "v3", "v4"]:
        for m in ["exact", "containment"]:
            d = one(CELLS[(v, m)], m); data[f"{v}_{m}"] = d
            print(f"{v+' '+CFG[v]:24.24} {m:12} {d['n']:5} {d['n_scored']:7} "
                  f"{(d['AUROC'] if d['AUROC'] is not None else float('nan')):7.4f}  "
                  f"{d['cov@5%']*100:4.1f} {d['cov@10%']*100:4.1f} {d['cov@20%']*100:4.1f}")
    mp = V2 / "paper" / "structured_vrdu_metrics.json"
    J = json.loads(mp.read_text()); J["auroc_coverage_present"] = data
    mp.write_text(json.dumps(J, indent=2))
    print(f"\n-> merged 'auroc_coverage_present' into {mp}")


if __name__ == "__main__":
    main()
