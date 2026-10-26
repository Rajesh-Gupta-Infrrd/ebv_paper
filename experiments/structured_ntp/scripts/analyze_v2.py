#!/usr/bin/env python3
"""Analyze a v2 task's decisions.jsonl -> metrics + risk-coverage + paper md.
Usage: analyze_v2.py --task {task1|task3a|task3b}"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
V2 = EBV / "experiments" / "structured_ntp/fatura"
TASK_DIR = {"task1": V2 / "task1_predroi_containment",
            "task3a": V2 / "task3a_predroi_exact",
            "task3b": V2 / "task3b_gt_endtoend_exact"}
TASK_DESC = {
    "task1": "Prediction-based ROI + CONTAINMENT correctness + ALL layers (calibration, keyword, empty)",
    "task3a": "Prediction-based ROI + EXACT correctness (clean GT) + ALL layers",
    "task3b": "Production end-to-end: GT-based ROI + EXACT correctness + ALL layers (no workarounds)",
}


def confusion(pop):
    TN = sum(1 for r in pop if r["correct"] and r["accept"])
    FP = sum(1 for r in pop if r["correct"] and not r["accept"])
    TP = sum(1 for r in pop if not r["correct"] and not r["accept"])
    FN = sum(1 for r in pop if not r["correct"] and r["accept"])
    wrong, corr = TP + FN, TN + FP
    return {"n": len(pop), "correct": corr, "wrong": wrong,
            "TN_correct_accept": TN, "FP_correct_route": FP,
            "TP_wrong_route": TP, "FN_wrong_accept": FN,
            "error_rate": round(wrong / len(pop), 4) if pop else None,
            "error_catch_rate": round(TP / wrong, 4) if wrong else None,
            "false_alarm_rate": round(FP / corr, 4) if corr else None,
            "route_precision": round(TP / (TP + FP), 4) if (TP + FP) else None}


def risk_coverage(pop):
    N = len(pop)
    wrong = sum(1 for r in pop if not r["correct"])
    corr = N - wrong
    elig = [(r["wv_score"], r["correct"]) for r in pop if r.get("wv_score") is not None]
    rows = []
    for i in range(101):
        t = i / 100.0
        acc = [c for (s, c) in elig if s >= t]
        na = len(acc); aw = sum(1 for c in acc if not c)
        cov = na / N if N else 0.0
        risk = aw / na if na else 0.0
        ec = (wrong - aw) / wrong if wrong else 0.0
        fa = (corr - (na - aw)) / corr if corr else 0.0
        rows.append((t, round(cov, 4), round(risk, 4), round(ec, 4), round(fa, 4)))
    pts = sorted({(c, rk) for _, c, rk, _, _ in rows})
    aurc = sum((b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in zip(pts, pts[1:]))
    return rows, round(aurc, 4)


def doc_level(pop):
    by = {}
    for r in pop:
        by.setdefault(r["doc"], []).append(r)
    docs = len(by)
    err = {d: any(not u["correct"] for u in us) for d, us in by.items()}
    acc = {d: all(u["accept"] for u in us) for d, us in by.items()}
    ed = sum(err.values()); cd = docs - ed
    er = sum(1 for d in by if err[d] and not acc[d])
    ca = sum(1 for d in by if not err[d] and acc[d])
    return {"docs": docs, "error_docs": ed, "clean_docs": cd,
            "doc_error_catch_rate": round(er / ed, 4) if ed else None,
            "doc_false_alarm_rate": round((cd - ca) / cd, 4) if cd else None}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--task", required=True, choices=list(TASK_DIR))
    args = ap.parse_args(); tdir = TASK_DIR[args.task]
    recs = [json.loads(l) for l in open(tdir / "decisions.jsonl")]
    pop = [r for r in recs if r.get("correct") is not None and r.get("accept") is not None]
    conf = confusion(pop)
    rows, aurc = risk_coverage(pop)
    dl = doc_level(pop)
    out = {"task": args.task, "desc": TASK_DESC[args.task], "rows_total": len(recs),
           "scored": len(pop), "confusion": conf, "AURC": aurc, "doc_level": dl}
    (tdir / "analysis").mkdir(exist_ok=True)
    (tdir / "analysis" / "metrics.json").write_text(json.dumps(out, indent=2))
    with open(tdir / "analysis" / "risk_coverage.csv", "w") as f:
        f.write("threshold,coverage,risk,error_catch,false_alarm\n")
        for row in rows:
            f.write(",".join(map(str, row)) + "\n")
    (tdir / "paper").mkdir(exist_ok=True)
    md = f"""# {args.task} — {TASK_DESC[args.task]}

Field-level (n={conf['n']}): error rate {conf['error_rate']*100:.1f}% ({conf['wrong']} wrong)
- **error-catch rate** {conf['error_catch_rate']}  ·  **false-alarm rate** {conf['false_alarm_rate']}  ·  route-precision {conf['route_precision']}
- AURC {aurc}
- confusion: TN(correct+accept)={conf['TN_correct_accept']} FP(correct+route)={conf['FP_correct_route']} TP(wrong+route)={conf['TP_wrong_route']} FN(wrong+accept)={conf['FN_wrong_accept']}

Document-level (accept iff all units accept): docs={dl['docs']} error_docs={dl['error_docs']}
- doc error-catch {dl['doc_error_catch_rate']}  ·  doc false-alarm {dl['doc_false_alarm_rate']}
"""
    (tdir / "paper" / "results.md").write_text(md)
    print(md)
    print(f"-> {tdir/'analysis'}/metrics.json, risk_coverage.csv ; paper/results.md")


if __name__ == "__main__":
    main()
