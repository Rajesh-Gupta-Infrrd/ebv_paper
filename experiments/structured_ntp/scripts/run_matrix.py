#!/usr/bin/env python3
"""
Controlled matrix runner: same NTP full pipeline, toggling ROI source / calibration /
correctness-for-calibration. Writes decisions (doc,field,tmpl,accept,wv_score) so a
separate analyzer can relabel with BOTH exact and containment correctness.

  --geom {pred,gt}     ROI geometry from correct predictions, or from clean GT
  --corr {containment,exact}  correctness used to pick 'correct' preds + calibrate
  --calib {on,off}     run weight/threshold calibration, or use NTP defaults
  --name NAME          output dir: structured_ntp/matrix/NAME/
"""
from __future__ import annotations
import argparse, json, os, re, sys, tempfile
from pathlib import Path

os.environ["NTP_RUN_WEIGHT_CALIBRATION"] = "0"
NTP_DIR = "/Users/rajeshgupta/Git_Clones/NTP/NTP"
sys.path.insert(0, NTP_DIR)
import compute_roi, evaluate_roi, calibrate_weights  # noqa: E402
from ntp_inference import FieldMapper  # noqa: E402

EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
EXP = EBV / "experiments"; V2 = EXP / "structured_ntp"

# Per-dataset config. FATURA is the original (default); VRDU reuses the SAME pipeline via
# OCR token files + a per-template split produced by prep_vrdu_roi.py.
DATASETS = {
    "fatura": {"res": "fatura_results", "ocr": "fatura_ocr", "split": "fatura_split.json",
               "gt_raw": "ground_truth_fatura.json", "gt_clean": "ground_truth_fatura_clean.json",
               "res_json": "extraction_results_fatura.json", "dt_prefix": "fatura_T", "test_ext": "jpg"},
    "vrdu":   {"res": "vrdu_results", "ocr": "vrdu_ocr", "split": "vrdu_split.json",
               "gt_raw": "ground_truth_vrdu.json", "gt_clean": "ground_truth_vrdu_clean.json",
               "res_json": "extraction_results_vrdu.json", "dt_prefix": "vrdu_", "test_ext": "pdf"},
}
# module globals set per --dataset in main() (toks/build_item read them)
RES = EXP / "results" / "fatura_results"
OCR_DIR = EXP / "structured_ntp" / "inputs" / "fatura_ocr"
SPLIT = EXP / "structured_ntp" / "splits" / "fatura_split.json"
TEST_EXT = "jpg"
_fm = FieldMapper(); _ALNUM = re.compile(r"[^a-z0-9]+"); _DUMMY = tempfile.mkdtemp(prefix="ntp_mx_")


def contain(p, g):
    p, g = _ALNUM.sub("", (p or "").lower()), _ALNUM.sub("", (g or "").lower())
    return (p == g if len(p) < 2 else (p in g or g in p)) if p and g else False


def nexact(g, p, f):
    try: return bool(compute_roi.values_match_field_aware(g, p, f))
    except TypeError: return bool(compute_roi.values_match_field_aware(g, p))


def toks(d):
    p = OCR_DIR / f"{d}.json"; return json.loads(p.read_text()) if p.exists() else []


def enrich(m, t): return _fm.enrich_fields({k: str(v) for k, v in m.items() if v is not None}, [dict(x) for x in t])


def _cands(v):
    """GT value -> list of non-empty candidate strings (handles VRDU multi-value list GT)."""
    if v is None:
        return []
    xs = v if isinstance(v, list) else [v]
    return [str(x) for x in xs if x is not None and str(x).strip() != ""]


def _rep_gt(v, pred, f, exact=True):
    """A single representative GT string for geometry/original: prefer the element that
    matches the prediction (so ROI/enrichment uses the value actually located), else first."""
    cs = _cands(v)
    if not cs:
        return None
    if pred is not None:
        for c in cs:
            if (nexact(c, str(pred), f) if exact else contain(str(pred), c)):
                return c
    return cs[0]


def build_item(doc, raw, clean, pred, geom, corr, present_only=False):
    t = toks(doc); pnn = {f: v for f, v in pred.items() if v is not None}
    if present_only:  # drop absent-field hallucinations BEFORE the pipeline sees them
        pnn = {f: v for f, v in pnn.items() if _cands(raw.get(f))}
    if corr == "containment":
        correct = {f: any(contain(str(pred[f]), c) for c in _cands(raw.get(f))) for f in pnn if _cands(raw.get(f))}
        original = {f: (str(pred[f]) if correct.get(f) else f"__W_{f}__") for f in correct}
    else:
        correct = {f: any(nexact(c, str(pred[f]), f) for c in _cands(clean.get(f))) for f in pnn if _cands(clean.get(f))}
        original = {f: _rep_gt(clean.get(f), pred.get(f), f, exact=True) for f in clean if _cands(clean.get(f))}
    if geom == "gt":
        geom_map = {f: _rep_gt(clean.get(f), pred.get(f), f, exact=(corr == "exact")) for f in clean if _cands(clean.get(f))}
    else:
        geom_map = {f: str(pred[f]) for f in correct if correct.get(f)}
    return {"status": "processed", "documentId": doc, "testFilename": f"{doc}.{TEST_EXT}",
            "original": original, "extracted_actual": {f: str(pred[f]) for f in pnn},
            "enriched_original": enrich(geom_map, t),
            "enriched_extracted_actual": enrich({f: str(pred[f]) for f in pnn}, t)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geom", required=True, choices=["pred", "gt"])
    ap.add_argument("--corr", required=True, choices=["containment", "exact"])
    ap.add_argument("--calib", required=True, choices=["on", "off"])
    ap.add_argument("--name", required=True)
    ap.add_argument("--dataset", default="fatura", choices=list(DATASETS))
    ap.add_argument("--templates", default="all")
    ap.add_argument("--present-only", action="store_true", help="drop absent-field preds before the pipeline")
    a = ap.parse_args()
    global RES, OCR_DIR, SPLIT, TEST_EXT
    cfg = DATASETS[a.dataset]
    RES = EXP / "results" / cfg["res"]
    OCR_DIR = EXP / "structured_ntp" / "inputs" / cfg["ocr"]
    SPLIT = EXP / "structured_ntp" / "splits" / cfg["split"]
    TEST_EXT = cfg["test_ext"]
    out = V2 / a.dataset / "matrix" / a.name
    (out / "golden").mkdir(parents=True, exist_ok=True); (out / "test").mkdir(exist_ok=True); (out / "roi").mkdir(exist_ok=True)

    split = json.loads(SPLIT.read_text())
    raw = json.loads((RES / cfg["gt_raw"]).read_text())
    clean = json.loads((V2 / "gt_clean" / cfg["gt_clean"]).read_text())
    res = json.loads((RES / cfg["res_json"]).read_text())
    ex = next(iter(next(iter(res.values())).keys()))
    pof = lambda d: (res.get(d, {}).get(ex, {}).get("extracted")) or {}
    keys = list(split["per_template"])
    if a.templates != "all":
        tmpls = a.templates.split(",")
    elif all(str(k).isdigit() for k in keys):
        tmpls = sorted(keys, key=lambda t: int(t))
    else:
        tmpls = sorted(keys)

    dec = open(out / "decisions.jsonl", "w")
    for tmpl in tmpls:
        rec = split["per_template"][tmpl]
        # sanitize to a filesystem/doctype-safe label (keeps FATURA's exact "fatura_T{n}")
        dt = re.sub(r"[^A-Za-z0-9]+", "_", cfg["dt_prefix"] + str(tmpl)).strip("_")
        g = {"docType": dt, "userModelId": "", "items": [build_item(d, raw[d], clean[d], pof(d), a.geom, a.corr, a.present_only) for d in rec["train"]]}
        t = {"docType": dt, "userModelId": "", "items": [build_item(d, raw[d], clean[d], pof(d), a.geom, a.corr, a.present_only) for d in rec["test"]]}
        gp = out / "golden" / f"{dt}.json"; tp = out / "test" / f"{dt}.json"
        gp.write_text(json.dumps(g)); tp.write_text(json.dumps(t))
        compute_roi.compute_roi_for_doc_type(gp, out / "roi", threshold_method="percentile_15_85", use_actual_extraction=True)
        rp = out / "roi" / f"{dt}_roi.json"
        if a.calib == "on":
            try:
                dfg = evaluate_roi.evaluate_doc_type(gp, rp, evaluate_ground_truth=False, input_dir=_DUMMY, use_actual_extraction=True, skip_roi_embedded_eval=True)
                calibrate_weights.calibrate_from_evaluation_dataframes(dfg, rp, use_actual_extraction=True)
            except Exception as e:
                print(f"  [{dt}] calib skip: {e}")
        dft = evaluate_roi.evaluate_doc_type(tp, rp, evaluate_ground_truth=False, input_dir=_DUMMY, use_actual_extraction=True)
        def col(df, *s):
            for c in df.columns:
                if all(x in c.lower() for x in s): return c
        cp, cw, cov = col(dft, "final_pass"), col(dft, "weighted_vote"), col(dft, "overlap_score")
        for _, r in dft.iterrows():
            wv = r.get(cw) if cw else None
            dec.write(json.dumps({"doc": r.get("documentId"), "tmpl": tmpl, "field": r.get("fieldName"),
                                  "accept": bool(r.get(cp)) if cp else None,
                                  "wv_score": float(wv) if wv is not None and str(wv) != "nan" else None}, default=str) + "\n")
        print(f"{dt}: {len(dft)} rows")
    dec.close(); print(f"-> {out/'decisions.jsonl'}")


if __name__ == "__main__":
    raise SystemExit(main())
