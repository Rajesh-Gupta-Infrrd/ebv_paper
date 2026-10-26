#!/usr/bin/env python3
"""
Build the controlled 8-row comparison table. Correctness (exact/containment) is just a
LABEL applied to the same accept/route decisions, so each decisions file is relabeled both
ways and scored uniformly.

8 cells (version x correctness):
  v1 = pred-ROI, NO calibration     (defaults)   -> matrix/v1_pred_nocalib
  v2 = pred-ROI, calibrated + layers              -> task3a (exact) / task1 (containment)
  v3 = GT-ROI,  calibrated + layers (production)  -> task3b (exact) / matrix/v3cont_gt_calib_contain (containment)
  v4 = GT-ROI,  NO calibration      (defaults)    -> matrix/v4_gt_nocalib
(calibration is correctness-specific, so v2/v3 use the correctness-matched calibrated run;
 v1/v4 are calibration-free so one run serves both labels.)
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

NTP_DIR = "/Users/rajeshgupta/Git_Clones/NTP/NTP"; sys.path.insert(0, NTP_DIR)
import compute_roi  # noqa: E402

EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
EXP = EBV / "experiments"; V2 = EXP / "structured_ntp/fatura"; RES = EXP / "results" / "fatura_results"
_ALNUM = re.compile(r"[^a-z0-9]+")

RAW = json.loads((RES / "ground_truth_fatura.json").read_text())
CLEAN = json.loads((V2 / "gt_clean" / "ground_truth_fatura_clean.json").read_text())
R = json.loads((RES / "extraction_results_fatura.json").read_text())
EXk = next(iter(next(iter(R.values())).keys()))


def pred_of(d, f):
    return (R.get(d, {}).get(EXk, {}).get("extracted") or {}).get(f)


def contain(p, g):
    p, g = _ALNUM.sub("", (p or "").lower()), _ALNUM.sub("", (g or "").lower())
    return (p == g if len(p) < 2 else (p in g or g in p)) if p and g else False


def nexact(g, p, f):
    try: return bool(compute_roi.values_match_field_aware(g, p, f))
    except TypeError: return bool(compute_roi.values_match_field_aware(g, p))


CELLS = {
    ("v1", "exact"): "matrix/v1_pred_nocalib/decisions.jsonl",
    ("v1", "containment"): "matrix/v1_pred_nocalib/decisions.jsonl",
    ("v2", "exact"): "task3a_predroi_exact/decisions.jsonl",
    ("v2", "containment"): "task1_predroi_containment/decisions.jsonl",
    ("v3", "exact"): "task3b_gt_endtoend_exact/decisions.jsonl",
    ("v3", "containment"): "matrix/v3cont_gt_calib_contain/decisions.jsonl",
    ("v4", "exact"): "matrix/v4_gt_nocalib/decisions.jsonl",
    ("v4", "containment"): "matrix/v4_gt_nocalib/decisions.jsonl",
}
VERS = {"v1": "pred-ROI, NO calib", "v2": "pred-ROI, calib+layers",
        "v3": "GT-ROI, calib+layers (prod)", "v4": "GT-ROI, NO calib"}


def correctness(doc, field, pred, mode):
    # present-field population only: skip rows where the field is absent in GT
    # (absent-field hallucinations are a separate, trivially-caught error type).
    if pred is None:
        return None
    if mode == "exact":
        cg = CLEAN.get(doc, {}).get(field)
        return nexact(cg, str(pred), field) if cg is not None else None
    rg = RAW.get(doc, {}).get(field)
    return contain(str(pred), rg) if rg is not None else None


def metrics(path, mode):
    TN = FP = TP = FN = 0
    elig = []
    n = 0
    for l in open(V2 / path):
        r = json.loads(l)
        p = pred_of(r["doc"], r["field"])
        c = correctness(r["doc"], r["field"], p, mode)
        if c is None or r.get("accept") is None:
            continue
        a = bool(r["accept"]); n += 1
        if c and a: TN += 1
        elif c and not a: FP += 1
        elif (not c) and (not a): TP += 1
        else: FN += 1
        if r.get("wv_score") is not None:
            elig.append((r["wv_score"], c))
    wrong, corr = TP + FN, TN + FP
    # AURC: sweep threshold over eligible (wv present); unlisted always routed
    rows = []
    for i in range(101):
        t = i / 100.0
        acc = [c for s, c in elig if s >= t]
        na = len(acc); aw = sum(1 for c in acc if not c)
        rows.append((na / n if n else 0, (aw / na if na else 0)))
    pts = sorted(set(rows)); aurc = sum((b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in zip(pts, pts[1:]))
    return {"n": n, "err": wrong / n if n else 0,
            "catch": TP / wrong if wrong else None, "fa": FP / corr if corr else None,
            "routeP": TP / (TP + FP) if (TP + FP) else None,
            "acc": (TP + TN) / n if n else None, "aurc": aurc}


def main():
    hdr = ("| version | config | correctness | n | err-rate | error-catch ↑ | false-alarm ↓ | "
           "route-prec ↑ | accuracy ↑ | AURC ↓ |")
    sep = "|" + "---|" * 10
    lines = [hdr, sep]
    missing = []
    for ver in ["v1", "v2", "v3", "v4"]:
        for mode in ["exact", "containment"]:
            path = CELLS[(ver, mode)]
            if not (V2 / path).exists():
                missing.append(path); continue
            m = metrics(path, mode)
            def f(x): return "—" if x is None else f"{x:.4f}"
            lines.append(f"| {ver} | {VERS[ver]} | {mode} | {m['n']} | {m['err']:.3f} | "
                         f"{f(m['catch'])} | {f(m['fa'])} | {f(m['routeP'])} | {f(m['acc'])} | {f(m['aurc'])} |")
    table = "\n".join(lines)
    (V2 / "paper" / "matrix_table.md").write_text(
        "# Controlled 8-way comparison (structured ROI, FATURA)\n\n"
        "↑ = higher is better, ↓ = lower is better. Correctness is a label on the SAME accept/route decisions.\n\n"
        + table + "\n")
    print(table)
    if missing:
        print("\nMISSING (runs not finished yet):", missing)


if __name__ == "__main__":
    main()
