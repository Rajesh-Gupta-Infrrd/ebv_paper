#!/usr/bin/env python3
"""Generate the VRDU structured-ROI results (present + full 8-row tables + per-field
breakdown) straight from the vrdu_* decision files. Mirrors doc_structured.py's metric
definitions exactly; adds list-GT handling (VRDU multi-value) and VRDU paths/CELLS.
Writes paper/STRUCTURED_VRDU.md and paper/structured_vrdu_metrics.json."""
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


CELLS = {("v1", "exact"): "matrix/vrdu_v1_pred_nocalib/decisions.jsonl", ("v1", "containment"): "matrix/vrdu_v1_pred_nocalib/decisions.jsonl",
         ("v2", "exact"): "matrix/vrdu_v2_pred_exact/decisions.jsonl", ("v2", "containment"): "matrix/vrdu_v2_pred_contain/decisions.jsonl",
         ("v3", "exact"): "matrix/vrdu_v3_gt_exact/decisions.jsonl", ("v3", "containment"): "matrix/vrdu_v3_gt_contain/decisions.jsonl",
         ("v4", "exact"): "matrix/vrdu_v4_gt_nocalib/decisions.jsonl", ("v4", "containment"): "matrix/vrdu_v4_gt_nocalib/decisions.jsonl"}
CFG = {"v1": "pred-ROI, calib OFF", "v2": "pred-ROI, calib ON", "v3": "GT-ROI, calib ON (prod)", "v4": "GT-ROI, calib OFF"}


def confusion_rows(path, mode, pop):
    TN = FP = TP = FN = 0; elig = []
    for l in open(V2 / path):
        r = json.loads(l)
        if r.get("accept") is None: continue
        c = corr(r["doc"], r["field"], mode, pop)
        if c is None: continue
        a = bool(r["accept"])
        if c and a: TN += 1
        elif c and not a: FP += 1
        elif not c and not a: TP += 1
        else: FN += 1
        if r.get("wv_score") is not None: elig.append((r["wv_score"], c))
    return TN, FP, TP, FN, elig


def metrics(path, mode, pop):
    TN, FP, TP, FN, elig = confusion_rows(path, mode, pop)
    n = TN + FP + TP + FN; w = TP + FN; co = TN + FP
    pts = []
    for i in range(101):
        t = i / 100; acc = [c for s, c in elig if s >= t]; na = len(acc); aw = sum(1 for c in acc if not c)
        pts.append((na / n if n else 0, aw / na if na else 0))
    pts = sorted(set(pts)); aurc = sum((b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in zip(pts, pts[1:]))
    d = {"n": n, "err_rate": round(w / n, 4) if n else None,
         "error_catch": round(TP / w, 4) if w else None,
         "false_alarm": round(FP / co, 4) if co else None,
         "route_prec": round(TP / (TP + FP), 4) if (TP + FP) else None,
         "accuracy": round((TP + TN) / n, 4) if n else None, "AURC": round(aurc, 4)}
    fmt = lambda x: "—" if x is None else (f"{x:.4f}" if isinstance(x, float) else str(x))
    row = (f"| {{v}} | {{cfg}} | {mode} | {n} | {w/n:.3f} | {fmt(d['error_catch'])} | {fmt(d['false_alarm'])} | "
           f"{fmt(d['route_prec'])} | {fmt(d['accuracy'])} | {fmt(d['AURC'])} |")
    return row, d


def table(pop):
    hdr = ("| ver | config | correctness | n | err-rate | error-catch ↑ | false-alarm ↓ | route-prec ↑ | accuracy ↑ | AURC ↓ |\n"
           "|---|---|---|---|---|---|---|---|---|---|")
    rows = [hdr]; data = {}
    for v in ["v1", "v2", "v3", "v4"]:
        for m in ["exact", "containment"]:
            row, d = metrics(CELLS[(v, m)], m, pop)
            rows.append(row.format(v=v, cfg=CFG[v])); data[f"{v}_{m}"] = d
    return "\n".join(rows), data


def per_field(path="matrix/vrdu_v3_gt_exact/decisions.jsonl", mode="exact", pop="present"):
    """Per-field present/exact breakdown for the production (v3 GT-ROI) config — surfaces the
    file_date date-normalization caveat and field-level spatial detectability."""
    from collections import defaultdict
    agg = defaultdict(lambda: [0, 0, 0, 0])  # TN,FP,TP,FN
    for l in open(V2 / path):
        r = json.loads(l)
        if r.get("accept") is None: continue
        c = corr(r["doc"], r["field"], mode, pop)
        if c is None: continue
        a = bool(r["accept"]); f = r["field"]
        idx = 0 if (c and a) else 1 if (c and not a) else 2 if (not c and not a) else 3
        agg[f][idx] += 1
    rows = ["| field | n | err-rate | error-catch ↑ | false-alarm ↓ | accuracy ↑ |", "|---|---|---|---|---|---|"]
    out = {}
    for f in sorted(agg):
        TN, FP, TP, FN = agg[f]; n = TN + FP + TP + FN; w = TP + FN; co = TN + FP
        ec = TP / w if w else None; fa = FP / co if co else None; ac = (TP + TN) / n if n else None
        g = lambda x: "—" if x is None else f"{x:.3f}"
        rows.append(f"| {f} | {n} | {w/n:.3f} | {g(ec)} | {g(fa)} | {g(ac)} |")
        out[f] = {"n": n, "err_rate": round(w / n, 4) if n else None,
                  "error_catch": round(ec, 4) if ec is not None else None,
                  "false_alarm": round(fa, 4) if fa is not None else None,
                  "accuracy": round(ac, 4) if ac is not None else None}
    return "\n".join(rows), out


def main():
    PRES, dp = table("present"); FULL, df = table("full")
    PF, pfd = per_field()
    (V2 / "paper" / "structured_vrdu_metrics.json").write_text(json.dumps(
        {"present": dp, "full": df, "per_field_v3_present_exact": pfd}, indent=2))
    doc = f"""# Structured (ROI) NTP — VRDU robustness results

Same NTP spatial ROI pipeline as the FATURA leg (no extra LLM/VLM call), on **VRDU
Registration-Forms (FARA)**: **1,915 REAL documents**, 3 form templates (Short-Form 789,
Amendment 709, Dissemination Report 417), 6 fields, per-field boxes. Extractor = NuExtract-3.
Per-template 70/30 split (seed 42): 1,340 train / 575 test. ROI geometry/evaluate driven offline
via NTP's venv; OCR token boxes come from VRDU's `dataset.jsonl` (no page images needed).
This is the **real-document counterpart to synthetic FATURA** for the structured channel.

## Versions & axes (identical to the FATURA leg)
v1 pred-ROI/calib-OFF · v2 pred-ROI/calib-ON · v3 GT-ROI/calib-ON (production) · v4 GT-ROI/calib-OFF.
Correctness is a LABEL on the same accept/route decisions: `exact` = NTP field-aware matcher on
cleaned GT; `containment` = normalized substring (lenient). Population: `present` = fields in the
doc's GT (honest spatial task); `full` = + absent-field hallucinations (trivially routed).
VRDU GT can be multi-value → correctness = prediction matches ANY GT occurrence.

## RESULTS — present-field population (honest spatial-detectability)
{PRES}

## RESULTS — full population (includes absent-field hallucinations)
{FULL}
*(↑ higher better, ↓ lower better.)*

## Per-field breakdown — production config v3 (GT-ROI, calib ON), present/exact
{PF}

> Note: NuExtract reformats dates to ISO (e.g. `2008-07-17`) which is not verbatim in the page
> OCR, so `file_date`'s predicted value is harder to localize spatially than the other fields —
> report it separately, as flagged in the data-provenance analysis.

## Data provenance
Predictions + GT: `experiments/results/vrdu_results/`. OCR token boxes + split + clean GT produced by
`scripts/prep_vrdu_roi.py` from `vrdu/registration-form/main/dataset.jsonl`
(`structured_ntp/inputs/vrdu_ocr/`, `structured_ntp/splits/vrdu_split.json`,
`gt_clean/ground_truth_vrdu_clean.json`). Matrix decisions under `matrix/vrdu_*`.
"""
    (V2 / "paper" / "STRUCTURED_VRDU.md").write_text(doc)
    print("PRESENT:\n" + PRES + "\n\nFULL:\n" + FULL + "\n\nPER-FIELD (v3 present/exact):\n" + PF)
    print(f"\n-> {V2/'paper'/'STRUCTURED_VRDU.md'}")


if __name__ == "__main__":
    main()
