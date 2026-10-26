#!/usr/bin/env python3
"""Fair FATURA AUROC/coverage: fix the EXACT-MATCH labeling artefact only.
Rule (per Rajesh 2026-10-21):
  A = value-right-but-exact-wrong (containment-tolerant, GT non-empty)  -> reclassify CORRECT
  B = GT-empty (sparsity, unverifiable model output)                    -> KEEP as error (no inflation)
  C = genuine wrong value in right place                                -> KEEP as error
Present-field. Scores (wv_score) come from the stored decision files; we only relabel correctness.
Also prints a 'drop-B' sensitivity line. Writes paper/fatura_clean_auroc_coverage.json. No model call."""
import json, re
from pathlib import Path
EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
EXP = EBV / "experiments"; V2 = EXP / "structured_ntp/fatura"; RES = EXP / "results" / "fatura_results"
R = json.loads((RES / "extraction_results_fatura.json").read_text())
GT = json.loads((RES / "ground_truth_fatura.json").read_text())
EXk = next(iter(next(iter(R.values())).keys()))
AL = re.compile(r"[^a-z0-9]+")


def pof(d, f): return (R.get(d, {}).get(EXk, {}).get("extracted") or {}).get(f)
def norm(x): return AL.sub("", str(x).lower()) if x is not None else ""
def contain(p, g):
    p, g = norm(p), norm(g)
    if not p or not g: return False
    return (p == g) if len(p) < 2 else (p in g or g in p)
def gt_empty(g): return g is None or str(g).strip().lower() in ("", "none")


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


def cov_at_risk(rows, targets=(0.05, 0.10, 0.20)):
    n = len(rows); scored = [(s, c) for s, c in rows if s is not None]; out = {}
    for tgt in targets:
        best = 0.0
        for i in range(101):
            t = i / 100; acc = [c for s, c in scored if s >= t]
            if not acc: continue
            if sum(1 for c in acc if not c) / len(acc) <= tgt: best = max(best, len(acc) / n)
        out[tgt] = best
    return out


def clean_label(doc, field, exact_correct):
    """Return (label_bool, bucket) under the fair rule; label_bool None means 'exclude' (drop-B only)."""
    if exact_correct:
        return True, "correct"
    p = pof(doc, field); g = GT.get(doc, {}).get(field)
    if contain(p, g) and not gt_empty(g):
        return True, "A->correct"
    if gt_empty(g):
        return False, "B(kept-error)"
    return False, "C(kept-error)"


def run(tag, path):
    rows_keepB, rows_dropB = [], []; buckets = {}
    for l in open(V2 / path):
        r = json.loads(l); ec = r.get("correct")
        if ec is None: continue
        p = pof(r["doc"], r["field"])
        if p is None or str(p).strip() == "": continue   # present
        s = r.get("wv_score")
        if isinstance(s, float) and s != s: s = None
        lab, b = clean_label(r["doc"], r["field"], bool(ec))
        buckets[b] = buckets.get(b, 0) + 1
        rows_keepB.append((s, lab))
        if b != "B(kept-error)": rows_dropB.append((s, lab))

    def summ(rows):
        n = len(rows); err = sum(1 for _, c in rows if not c)
        a = auroc([(s, c) for s, c in rows if s is not None]); cov = cov_at_risk(rows)
        return {"n": n, "err_rate": round(err / n, 4), "AUROC": round(a, 4) if a is not None else None,
                "cov@5%": round(cov[0.05], 4), "cov@10%": round(cov[0.10], 4), "cov@20%": round(cov[0.20], 4)}
    return {"buckets": buckets, "fair_keepB": summ(rows_keepB), "sensitivity_dropB": summ(rows_dropB)}


OUT = {}
for tag, path in [("v2_predROI", "task3a_predroi_exact/decisions.jsonl"),
                  ("v3_gtROI_prod", "task3b_gt_endtoend_exact/decisions.jsonl")]:
    OUT[tag] = run(tag, path)
    d = OUT[tag]
    print(f"\n### {tag}")
    print("  buckets:", d["buckets"])
    f = d["fair_keepB"]; s = d["sensitivity_dropB"]
    print(f"  FAIR (A->correct, keep B&C): n={f['n']} err={f['err_rate']} AUROC={f['AUROC']} "
          f"cov@5/10/20={f['cov@5%']*100:.1f}/{f['cov@10%']*100:.1f}/{f['cov@20%']*100:.1f}%")
    print(f"  sensitivity (also drop B)  : n={s['n']} err={s['err_rate']} AUROC={s['AUROC']} "
          f"cov@5/10/20={s['cov@5%']*100:.1f}/{s['cov@10%']*100:.1f}/{s['cov@20%']*100:.1f}%")

(V2 / "paper" / "fatura_clean_auroc_coverage.json").write_text(json.dumps(OUT, indent=2))
print(f"\n-> {V2/'paper'/'fatura_clean_auroc_coverage.json'}")
