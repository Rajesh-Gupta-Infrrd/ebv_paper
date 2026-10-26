#!/usr/bin/env python3
"""Analyze Signal decisions -> metrics (binary + 3-tier, scalar-only + all fields):
error-catch, false-alarm, route-precision, accuracy, AUROC, coverage@fixed-risk,
per-signal separation, and sufficiency (empty-prior usage). Writes analysis/ + paper/."""
from __future__ import annotations
import json
from pathlib import Path

EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
UNS = EBV / "experiments" / "unstructured_ntp"
RECS = [json.loads(l) for l in open(UNS / "realkie_fcc" / "decisions" / "fcc_decisions.jsonl")]


def score_of(r):
    return r["proba"] if r.get("proba") is not None else r.get("final_score")


def auroc(pairs):
    pos = [s for s, c in pairs if c]; neg = [s for s, c in pairs if not c]
    if not pos or not neg:
        return None
    allp = sorted(pairs, key=lambda x: x[0]); r = [0] * len(allp); j = 0
    while j < len(allp):
        k = j
        while k + 1 < len(allp) and allp[k + 1][0] == allp[j][0]:
            k += 1
        for t in range(j, k + 1):
            r[t] = (j + k) / 2 + 1
        j = k + 1
    sr = sum(r[i] for i, (s, c) in enumerate(allp) if c)
    return (sr - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def cov_at_risk(rows, targets=(0.05, 0.10, 0.20)):
    n = len(rows); scored = [(s, c) for s, c in rows if s is not None]
    out = {}
    for tgt in targets:
        best = 0.0
        for i in range(101):
            t = i / 100; acc = [c for s, c in scored if s >= t]
            if acc and sum(1 for c in acc if not c) / len(acc) <= tgt:
                best = max(best, len(acc) / n)
        out[tgt] = best
    return out


def confusion(rows, accept_key):
    TN = sum(1 for r in rows if r["correct"] and r[accept_key])
    FP = sum(1 for r in rows if r["correct"] and not r[accept_key])
    TP = sum(1 for r in rows if not r["correct"] and not r[accept_key])
    FN = sum(1 for r in rows if not r["correct"] and r[accept_key])
    n = TN + FP + TP + FN; w = TP + FN; co = TN + FP
    sc = [(score_of(r), r["correct"]) for r in rows if score_of(r) is not None]
    cov = cov_at_risk([(score_of(r), r["correct"]) for r in rows])
    return {"n": n, "wrong": w, "err_rate": round(w / n, 4) if n else None,
            "error_catch": round(TP / w, 4) if w else None,
            "false_alarm": round(FP / co, 4) if co else None,
            "route_prec": round(TP / (TP + FP), 4) if (TP + FP) else None,
            "accuracy": round((TP + TN) / n, 4) if n else None,
            "AUROC": round(auroc(sc), 4) if auroc(sc) is not None else None,
            "cov@5%": round(cov[0.05], 4), "cov@10%": round(cov[0.10], 4), "cov@20%": round(cov[0.20], 4)}


def main():
    out = {}
    for pop, filt in [("all", lambda r: True), ("scalar", lambda r: r.get("field_type") == "scalar")]:
        rows = [r for r in RECS if filt(r) and r.get("correct") is not None]
        out[pop] = {"binary": confusion(rows, "accept_bin"), "3tier": confusion(rows, "accept_3t")}
    # sufficiency / empty-prior usage + 3-tier breakdown
    out["sufficiency"] = {
        "empty_prior_applied": sum(1 for r in RECS if r.get("empty_prior_applied")),
        "gated": sum(1 for r in RECS if r.get("gated")),
        "tier3_breakdown": {k: sum(1 for r in RECS if r.get("decision_3t") == k)
                            for k in ["NTP", "LLM_REVIEW", "HUMAN_REVIEW"]},
    }
    # per-signal separation (mean signal value for correct vs wrong), binary core signals
    sig_names = ["format_valid", "keyword_context", "source_context", "value_in_text",
                 "label_value_distance", "partial_extraction"]
    persig = {}
    for s in sig_names:
        def vals(correct):
            xs = [r["signals"].get(s) for r in RECS if r.get("signals") and r["correct"] == correct
                  and isinstance(r["signals"].get(s), (int, float))]
            return round(sum(xs) / len(xs), 3) if xs else None
        persig[s] = {"mean_correct": vals(True), "mean_wrong": vals(False)}
    out["per_signal_mean"] = persig

    (UNS / "realkie_fcc" / "analysis").mkdir(exist_ok=True)
    (UNS / "realkie_fcc" / "analysis" / "signal_metrics.json").write_text(json.dumps(out, indent=2))
    # paper md
    def row(tag, m):
        return (f"| {tag} | {m['n']} | {m['err_rate']} | {m['error_catch']} | {m['false_alarm']} | "
                f"{m['route_prec']} | {m['accuracy']} | {m['AUROC']} | {m['cov@5%']} |")
    md = ["# Signal (unstructured) NTP — FCC results", "",
          "| population / mode | n | err-rate | error-catch ↑ | false-alarm ↓ | route-prec ↑ | accuracy ↑ | AUROC ↑ | cov@5% ↑ |",
          "|---|---|---|---|---|---|---|---|---|"]
    for pop in ["all", "scalar"]:
        md.append(row(f"{pop} / binary", out[pop]["binary"]))
        md.append(row(f"{pop} / 3tier", out[pop]["3tier"]))
    md.append("")
    md.append(f"Sufficiency: empty_prior_applied={out['sufficiency']['empty_prior_applied']}, "
              f"gated={out['sufficiency']['gated']}, 3-tier={out['sufficiency']['tier3_breakdown']}")
    (UNS / "paper").mkdir(exist_ok=True)
    (UNS / "paper" / "signal_results.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\n-> {UNS/'analysis'/'signal_metrics.json'} ; paper/signal_results.md")


if __name__ == "__main__":
    main()
