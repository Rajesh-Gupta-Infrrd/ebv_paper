#!/usr/bin/env python3
"""Compare Signal decisions across runs (e.g. untuned vs tuned). Prints scalar + all
metrics (binary mode) for each decisions file side by side."""
import json, sys
from pathlib import Path
UNS = Path(__file__).resolve().parents[1]


def auroc(pairs):
    pos = [s for s, c in pairs if c]; neg = [s for s, c in pairs if not c]
    if not pos or not neg:
        return None
    allp = sorted(pairs); r = [0] * len(allp); j = 0
    while j < len(allp):
        k = j
        while k + 1 < len(allp) and allp[k + 1][0] == allp[j][0]:
            k += 1
        for t in range(j, k + 1):
            r[t] = (j + k) / 2 + 1
        j = k + 1
    sr = sum(r[i] for i, (s, c) in enumerate(allp) if c)
    return (sr - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def cov5(rows):
    n = len(rows); sc = [(s, c) for s, c in rows if s is not None]
    best = 0.0
    for i in range(101):
        t = i / 100; acc = [c for s, c in sc if s >= t]
        if acc and sum(1 for c in acc if not c) / len(acc) <= 0.05:
            best = max(best, len(acc) / n)
    return best


def metrics(recs, scalar_only):
    rows = [r for r in recs if r.get("correct") is not None and (not scalar_only or r.get("field_type") == "scalar")]
    TN = sum(1 for r in rows if r["correct"] and r["accept_bin"])
    FP = sum(1 for r in rows if r["correct"] and not r["accept_bin"])
    TP = sum(1 for r in rows if not r["correct"] and not r["accept_bin"])
    FN = sum(1 for r in rows if not r["correct"] and r["accept_bin"])
    n = len(rows); w = TP + FN; co = TN + FP
    sc = lambda r: r["proba"] if r.get("proba") is not None else r.get("final_score")
    au = auroc([(sc(r), r["correct"]) for r in rows if sc(r) is not None])
    cv = cov5([(sc(r), r["correct"]) for r in rows])
    return dict(n=n, catch=round(TP / w, 3) if w else None, fa=round(FP / co, 3) if co else None,
                acc=round((TP + TN) / n, 3) if n else None,
                auroc=round(au, 4) if au is not None else None, cov5=round(cv, 3))


def main():
    files = sys.argv[1:] or ["decisions/fcc_decisions.jsonl", "decisions/fcc_decisions_tuned.jsonl"]
    print(f"{'run':30} {'pop':8} {'n':>5} {'catch':>7} {'FA':>7} {'acc':>7} {'AUROC':>7} {'cov@5%':>7}")
    for f in files:
        p = UNS / f
        if not p.exists():
            print(f"{f:30} MISSING"); continue
        recs = [json.loads(l) for l in open(p)]
        for scalar in (True, False):
            m = metrics(recs, scalar)
            print(f"{Path(f).stem:30} {'scalar' if scalar else 'all':8} {m['n']:>5} "
                  f"{m['catch']!s:>7} {m['fa']!s:>7} {m['acc']!s:>7} {m['auroc']!s:>7} {m['cov5']!s:>7}")


if __name__ == "__main__":
    main()
