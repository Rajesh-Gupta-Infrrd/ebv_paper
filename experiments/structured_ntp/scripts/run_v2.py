#!/usr/bin/env python3
"""
Run the FULL NTP ROI pipeline (all layers ON) for the three v2 tasks, per template.

Pipeline per template (doc-type), offline (no Mongo):
  compute_roi.compute_roi_for_doc_type(golden)            -> ROI geometry + per-field thresholds + contextKeywords
  evaluate_roi.evaluate_doc_type(golden) -> df            -> train spatial scores + value_match
  calibrate_weights.calibrate_from_evaluation_dataframes  -> injects calibrated weights + score_threshold
  evaluate_roi.evaluate_doc_type(test)   -> df            -> ACCEPT/ROUTE per (doc,field), all layers applied

Tasks differ only in how golden/test are built:
  task1  : ROI geometry from CORRECT-by-CONTAINMENT predictions; correctness=containment
           (original fabricated so NTP's value_match reproduces containment labels)
  task3a : ROI geometry from CORRECT-by-EXACT predictions;        correctness=exact (original=clean GT)
  task3b : ROI geometry from CLEAN GT (production);               correctness=exact (original=clean GT)
All tasks: weight+threshold calibration, keyword boost, empty-field handling = ON.

Usage: run_v2.py --task {task1|task3a|task3b} [--templates all|1,2]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

os.environ["NTP_RUN_WEIGHT_CALIBRATION"] = "0"   # we calibrate explicitly below (controlled, no PDFs)
NTP_DIR = "/Users/rajeshgupta/Git_Clones/NTP/NTP"
sys.path.insert(0, NTP_DIR)
import compute_roi                     # noqa: E402
import evaluate_roi                    # noqa: E402
import calibrate_weights               # noqa: E402
from ntp_inference import FieldMapper  # noqa: E402

EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
EXP = EBV / "experiments"
V2 = EXP / "structured_ntp/fatura"
RES = EXP / "results" / "fatura_results"
OCR_DIR = EXP / "structured_ntp" / "inputs" / "fatura_ocr"
SPLIT = EXP / "structured_ntp" / "splits" / "fatura_split.json"

_fm = FieldMapper()
_ALNUM = re.compile(r"[^a-z0-9]+")
_DUMMY = tempfile.mkdtemp(prefix="ntp_v2_noinput_")

TASK_DIR = {"task1": V2 / "task1_predroi_containment",
            "task3a": V2 / "task3a_predroi_exact",
            "task3b": V2 / "task3b_gt_endtoend_exact"}


def contain(pred, gt) -> bool:
    p, g = _ALNUM.sub("", (pred or "").lower()), _ALNUM.sub("", (gt or "").lower())
    if not p or not g:
        return False
    return p == g if len(p) < 2 else (p in g or g in p)


def ntp_exact(gt, pred, field) -> bool:
    try:
        return bool(compute_roi.values_match_field_aware(gt, pred, field))
    except TypeError:
        return bool(compute_roi.values_match_field_aware(gt, pred))


def tokens(doc_id):
    p = OCR_DIR / f"{doc_id}.json"
    return json.loads(p.read_text()) if p.exists() else []


def enrich(value_map, toks):
    return _fm.enrich_fields({k: str(v) for k, v in value_map.items() if v is not None},
                             [dict(t) for t in toks])


def build_item(doc_id, raw_gt, clean_gt, pred, task):
    toks = tokens(doc_id)
    pred_nn = {f: v for f, v in pred.items() if v is not None}
    # correctness per field (present fields only -> clean_gt not None)
    if task == "task1":
        correct = {f: contain(str(pred[f]), raw_gt.get(f)) for f in pred_nn if raw_gt.get(f) is not None}
    else:
        correct = {f: ntp_exact(clean_gt.get(f), str(pred[f]), f) for f in pred_nn if clean_gt.get(f) is not None}

    # original: fabricate for task1 (encode containment); clean GT for 3a/3b
    if task == "task1":
        original = {f: (str(pred[f]) if correct.get(f) else f"__WRONG_{f}__") for f in correct}
    else:
        original = {f: clean_gt[f] for f in clean_gt if clean_gt[f] is not None}

    extracted_actual = {f: str(pred[f]) for f in pred_nn}

    # geometry source (enriched_original)
    if task == "task3b":
        geom_map = {f: clean_gt[f] for f in clean_gt if clean_gt[f] is not None}
    else:  # task1 / task3a: correct predictions' locations
        geom_map = {f: str(pred[f]) for f in correct if correct.get(f)}

    return {
        "status": "processed", "documentId": doc_id, "testFilename": f"{doc_id}.jpg",
        "original": original,
        "extracted_actual": extracted_actual,
        "enriched_original": enrich(geom_map, toks),
        "enriched_extracted_actual": enrich({f: str(pred[f]) for f in pred_nn}, toks),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=list(TASK_DIR))
    ap.add_argument("--templates", default="all")
    args = ap.parse_args()
    tdir = TASK_DIR[args.task]
    (tdir / "datasets" / "golden").mkdir(parents=True, exist_ok=True)
    (tdir / "datasets" / "test").mkdir(parents=True, exist_ok=True)
    (tdir / "roi_models").mkdir(parents=True, exist_ok=True)

    split = json.loads(SPLIT.read_text())
    raw = json.loads((RES / "ground_truth_fatura.json").read_text())
    clean = json.loads((V2 / "gt_clean" / "ground_truth_fatura_clean.json").read_text())
    res = json.loads((RES / "extraction_results_fatura.json").read_text())
    extractor = next(iter(next(iter(res.values())).keys()))

    def pred_of(d):
        return (res.get(d, {}).get(extractor, {}).get("extracted")) or {}

    tmpls = sorted(split["per_template"], key=lambda t: int(t)) \
        if args.templates == "all" else [t.strip() for t in args.templates.split(",")]

    dec_path = tdir / "decisions.jsonl"
    dec_f = open(dec_path, "w")
    cols_printed = False
    for tmpl in tmpls:
        rec = split["per_template"][tmpl]
        dt = f"fatura_T{tmpl}"
        golden = {"docType": dt, "userModelId": "",
                  "items": [build_item(d, raw[d], clean[d], pred_of(d), args.task) for d in rec["train"]]}
        test = {"docType": dt, "userModelId": "",
                "items": [build_item(d, raw[d], clean[d], pred_of(d), args.task) for d in rec["test"]]}
        gpath = tdir / "datasets" / "golden" / f"{dt}_golden.json"
        tpath = tdir / "datasets" / "test" / f"{dt}_test.json"
        gpath.write_text(json.dumps(golden))
        tpath.write_text(json.dumps(test))

        # learn ROI (+ thresholds + keywords), calibrate weights, then score test
        compute_roi.compute_roi_for_doc_type(gpath, tdir / "roi_models",
                                             threshold_method="percentile_15_85", use_actual_extraction=True)
        roi_path = tdir / "roi_models" / f"{dt}_roi.json"
        try:
            dfg = evaluate_roi.evaluate_doc_type(gpath, roi_path, evaluate_ground_truth=False,
                                                 input_dir=_DUMMY, use_actual_extraction=True,
                                                 skip_roi_embedded_eval=True)
            calibrate_weights.calibrate_from_evaluation_dataframes(dfg, roi_path, use_actual_extraction=True)
        except Exception as e:
            print(f"  [{dt}] calibration skipped: {type(e).__name__}: {e}")

        dft = evaluate_roi.evaluate_doc_type(tpath, roi_path, evaluate_ground_truth=False,
                                             input_dir=_DUMMY, use_actual_extraction=True)
        if not cols_printed:
            print("eval df columns:", list(dft.columns)); cols_printed = True
        # extract decisions defensively
        def col(df, *subs):
            for c in df.columns:
                lc = c.lower()
                if all(s in lc for s in subs):
                    return c
            return None
        c_doc = col(dft, "document") or col(dft, "doc", "id") or "documentId"
        c_field = col(dft, "field", "name") or col(dft, "field") or "fieldName"
        c_match = col(dft, "value_match") or col(dft, "value", "match")
        c_pass = col(dft, "final_pass")
        c_wv = col(dft, "weighted_vote") or col(dft, "weighted", "score")
        c_ov = col(dft, "overlap_score"); c_ce = col(dft, "center_score"); c_iou = col(dft, "iou_score")
        for _, r in dft.iterrows():
            correct = bool(r.get(c_match)) if c_match else None
            accept = bool(r.get(c_pass)) if c_pass else None
            wv = r.get(c_wv) if c_wv else None
            located = (r.get(c_ov) is not None) if c_ov else None
            dec_f.write(json.dumps({"doc": r.get(c_doc), "tmpl": tmpl, "field": r.get(c_field),
                                    "correct": correct, "accept": accept,
                                    "located": bool(located) if located is not None else None,
                                    "wv_score": float(wv) if wv is not None and str(wv) != "nan" else None,
                                    "overlap": r.get(c_ov) if c_ov else None,
                                    "center": r.get(c_ce) if c_ce else None,
                                    "iou": r.get(c_iou) if c_iou else None}, default=str) + "\n")
        print(f"{dt}: scored {len(dft)} rows")
    dec_f.close()
    print(f"-> {dec_path}")


if __name__ == "__main__":
    raise SystemExit(main())
