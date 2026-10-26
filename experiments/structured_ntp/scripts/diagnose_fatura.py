#!/usr/bin/env python3
"""Per-field diagnostic for FATURA v3 (GT-ROI, calib ON, exact) — mirror of diagnose_vrdu.py.
Is the lower FATURA AUROC a few bad field classes (outliers) or broad in-place value errors?
Reads the baked-in 'correct'/'wv_score'/'accept' from the decision file (present-field)."""
import json
from collections import defaultdict
from pathlib import Path
EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
V2 = EBV / "experiments" / "structured_ntp/fatura"
PATH = V2 / "task3b_gt_endtoend_exact" / "decisions.jsonl"


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


by_field = defaultdict(list)   # field -> (wv_score, correct)
acc_rows = defaultdict(list)   # field -> (correct, accept)
pooled = []
for l in open(PATH):
    r = json.loads(l)
    c = r.get("correct")
    if c is None: continue          # present-field = has a correctness label
    s = r.get("wv_score")
    if isinstance(s, float) and s != s: s = None   # NaN -> None (unlocated)
    if s is not None:
        by_field[r["field"]].append((s, bool(c))); pooled.append((s, bool(c)))
    if r.get("accept") is not None:
        acc_rows[r["field"]].append((bool(c), bool(r["accept"])))

# per-field table
print(f"{'field':16} {'n':>5} {'err%':>6} {'accept-all':>10} {'verifier':>9} {'AUROC':>7}")
stats = []
for f in sorted(by_field, key=lambda f: (auroc(by_field[f]) if auroc(by_field[f]) is not None else -1)):
    a = auroc(by_field[f]); ar = acc_rows[f]
    n = len(ar); err = sum(1 for c, _ in ar if not c) / n if n else 0
    vacc = sum(1 for c, ac in ar if (c and ac) or (not c and not ac)) / n if n else 0
    stats.append((f, len(by_field[f]), err, 1 - err, vacc, a))
    print(f"{f:16} {len(by_field[f]):5} {err*100:6.1f} {(1-err)*100:9.1f}% {vacc*100:8.1f}% "
          f"{('%.4f'%a) if a is not None else '  — ':>7}")

print(f"\nFields: {len(by_field)}   Pooled present/exact AUROC (v3 GT-ROI) = {auroc(pooled):.4f}  (n={len(pooled)})")
# distribution of per-field AUROC -> outlier vs broad?
aus = sorted(a for _, _, _, _, _, a in stats if a is not None)
import statistics
print(f"Per-field AUROC: min {aus[0]:.3f}  median {statistics.median(aus):.3f}  max {aus[-1]:.3f}  "
      f"(#fields<0.70: {sum(1 for a in aus if a<0.70)} / {len(aus)})")
# drop worst-k to see sensitivity
order = sorted(stats, key=lambda x: (x[5] if x[5] is not None else -1))
for k in (3, 5):
    drop = {order[i][0] for i in range(k)}
    sub = [p for f in by_field if f not in drop for p in by_field[f]]
    print(f"Excluding worst {k} fields ({', '.join(sorted(drop))}): AUROC {auroc(sub):.4f}")
