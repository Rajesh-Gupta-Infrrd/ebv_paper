#!/usr/bin/env python3
"""Diagnose WHY VRDU v3 AUROC/accuracy are lower than internal numbers.
Decompose by field: per-field AUROC + error composition, and recompute the pooled
AUROC/accuracy with the known date-normalization artefact field(s) removed.
Reuses exact-correctness logic from doc_structured_vrdu.py. No model call."""
import json, re, sys
from collections import defaultdict
from pathlib import Path
NTP = "/Users/rajeshgupta/Git_Clones/NTP/NTP"; sys.path.insert(0, NTP)
import compute_roi  # noqa
EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
EXP = EBV / "experiments"; V2 = EXP / "structured_ntp/vrdu"; RES = EXP / "results" / "vrdu_results"
AL = re.compile(r"[^a-z0-9]+")
RAW = json.loads((RES / "ground_truth_vrdu.json").read_text())
CLEAN = json.loads((V2 / "gt_clean" / "ground_truth_vrdu_clean.json").read_text())
R = json.loads((RES / "extraction_results_vrdu.json").read_text()); EXk = next(iter(next(iter(R.values())).keys()))
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")


def pof(d, f): return (R.get(d, {}).get(EXk, {}).get("extracted") or {}).get(f)
def cands(v):
    if v is None: return []
    xs = v if isinstance(v, list) else [v]
    return [str(x) for x in xs if x is not None and str(x).strip() != ""]
def nex(g, p, f):
    try: return bool(compute_roi.values_match_field_aware(g, p, f))
    except TypeError: return bool(compute_roi.values_match_field_aware(g, p))
def corr_exact(d, f):
    p = pof(d, f)
    if p is None: return None
    cg = cands(CLEAN.get(d, {}).get(f))
    if cg: return any(nex(c, str(p), f) for c in cg)
    return None  # present-field only


def auroc(pairs):
    pos = [s for s, c in pairs if c]; neg = [s for s, c in pairs if not c]
    if not pos or not neg: return None
    allp = sorted(pairs, key=lambda x: x[0]); r = [0.0] * len(allp); j = 0
    while j < len(allp):
        k = j
        while k + 1 < len(allp) and allp[k + 1][0] == allp[j][0]: k += 1
        avg = (j + k) / 2 + 1
        for t in range(j, k + 1): r[t] = avg
        j = k + 1
    sr = sum(r[idx] for idx, (s, c) in enumerate(allp) if c)
    return (sr - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


PATH = "matrix/vrdu_v3_gt_exact/decisions.jsonl"
by_field = defaultdict(list)   # field -> (wv_score, correct)
date_art = defaultdict(lambda: [0, 0])  # field -> [iso_pred_errors, total_errors]
for l in open(V2 / PATH):
    r = json.loads(l); f = r["field"]; c = corr_exact(r["doc"], f)
    if c is None: continue
    by_field[f].append((r.get("wv_score"), c))
    if not c:  # inspect error composition
        p = pof(r["doc"], f); date_art[f][1] += 1
        if p and ISO.match(str(p).strip()): date_art[f][0] += 1

print("=== Per-field (v3 GT-ROI, present/exact) ===")
print(f"{'field':24} {'n':>5} {'err%':>6} {'AUROC':>7} {'acc':>6}  {'ISO-date errs / total errs'}")
pooled, pooled_nofd = [], []
for f in sorted(by_field):
    rows = by_field[f]; n = len(rows); werr = sum(1 for _, c in rows if not c)
    scored = [(s, c) for s, c in rows if s is not None]
    a = auroc(scored)
    # accuracy = fraction correctly routed: accept(wv>=? ) — proxy: use correct-vs-accept not available here;
    # report correctness rate complement instead as context
    iso, tot = date_art[f]
    print(f"{f:24} {n:5} {werr/n*100:6.1f} {('%.4f'%a) if a is not None else '   —  ':>7} "
          f"{'':6}  {iso}/{tot} ({(iso/tot*100 if tot else 0):.0f}% of errors are ISO-reformatted dates)")
    pooled += scored
    if f != "file_date": pooled_nofd += scored

SIGNER = {"signer_name", "signer_title"}
FIXED = {"registration_num", "registrant_name", "file_date"}
pool_nosig = [p for f in by_field if f not in SIGNER for p in [(s, c) for s, c in by_field[f] if s is not None]]
pool_fixed = [p for f in by_field if f in FIXED for p in [(s, c) for s, c in by_field[f] if s is not None]]
print("\n=== Pooled AUROC (present/exact, v3) ===")
print(f"ALL fields                     : AUROC {auroc(pooled):.4f}  (n={len(pooled)})")
print(f"EXCLUDING file_date            : AUROC {auroc(pooled_nofd):.4f}  (n={len(pooled_nofd)})")
print(f"EXCLUDING signature fields     : AUROC {auroc(pool_nosig):.4f}  (n={len(pool_nosig)})")
print(f"FIXED-position fields only      : AUROC {auroc(pool_fixed):.4f}  (n={len(pool_fixed)})")
print("\n=== Per-field: does the verifier BEAT accept-all? (accept-all acc = 1 - err) ===")
# need the accept decision to compute routing accuracy; reload with accept
dec = {}
for l in open(V2 / PATH):
    r = json.loads(l)
    if r.get("accept") is not None: dec[(r["doc"], r["field"])] = bool(r["accept"])
print(f"{'field':24} {'err%':>6} {'accept-all acc':>14} {'verifier acc':>13} {'AUROC':>7}")
for f in sorted(by_field):
    rows = []
    for l in open(V2 / PATH):
        r = json.loads(l)
        if r["field"] != f: continue
        c = corr_exact(r["doc"], f)
        if c is None or (r["doc"], f) not in dec: continue
        rows.append((c, dec[(r["doc"], f)]))
    n = len(rows); err = sum(1 for c, _ in rows if not c) / n
    acc = sum(1 for c, a in rows if (c and a) or (not c and not a)) / n
    scored = [(s, c) for s, c in by_field[f] if s is not None]; a = auroc(scored)
    print(f"{f:24} {err*100:6.1f} {(1-err)*100:13.1f}% {acc*100:12.1f}% {('%.4f'%a) if a is not None else '  — ':>7}")
