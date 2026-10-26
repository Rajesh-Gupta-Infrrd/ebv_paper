#!/usr/bin/env python3
"""
Build the Signal-NTP input for RealKIE-FCC + an 80/20 doc split, from our existing
predictions + ground truth + document text. Keeps dociq untouched (we only produce
its expected input files here).

dociq record format (one per doc):
  {"documentId", "text", "NER_Output": {field: value_str},
   "entities": [{"fieldName": field, "groundTruth": gt_str}, ...]}

FCC quirk: several "Line Item - *" fields are MULTI-VALUE (a value per line item),
while NuExtract extracts ONE value. So correctness = MEMBERSHIP (pred matches ANY GT
value). We pick groundTruth = the matching GT element (so dociq's field-aware matcher
labels it correct), else the first element (labels incorrect). We tag each field
scalar vs lineitem and keep raw GT in a meta file for flexible analysis.

Writes:
  data/train/invoice.json, data/test/invoice.json     (dociq input)
  data/meta/train_meta.json, data/meta/test_meta.json  (doc->field-> {pred, gt, field_type, member})
  data/split.json
"""
from __future__ import annotations
import csv, json, random, re
from pathlib import Path

csv.field_size_limit(10**7)
EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
FCC = EBV / "realkie_fcc_invoices"
RES = EBV / "experiments" / "results" / "realkie_fcc_results"
OUT = EBV / "experiments" / "unstructured_ntp" / "data"
SEED, TRAIN_FRAC, DOC_TYPE = 42, 0.80, "invoice"
_ALNUM = re.compile(r"[^a-z0-9]+")


def norm(s):
    return _ALNUM.sub("", str(s).lower()) if s is not None else ""


def membership(pred, gt):
    """Return (status, gt_string_for_dociq). status: True=correct, False=wrong, None=UNLABELLED(drop).
    Multi-value -> pred matches ANY element. RealKIE GT is sparse: a field the annotators left
    absent while the extractor produced a plausible value is NOT a confirmed error, so we mark it
    None (dropped from train+eval) instead of labelling it wrong — which otherwise teaches the
    classifier to distrust good extractions and over-route."""
    cands = gt if isinstance(gt, list) else ([] if gt is None else [gt])
    cands = [c for c in cands if c is not None and str(c).strip() != ""]
    p = norm(pred)
    if not cands:                       # GT empty/absent
        if p == "":
            return (True, "")           # correct: model correctly extracted nothing
        return (None, "")               # pred present, GT unconfirmed -> UNLABELLED, drop
    if p == "":                         # pred empty but GT present -> real miss
        return (False, str(cands[0]))
    for c in cands:                     # membership via normalized containment
        nc = norm(c)
        if nc and (p == nc or p in nc or nc in p):
            return (True, str(c))
    return (False, str(cands[0]))


def text_map():
    m = {}
    with open(FCC / "train.csv", newline="") as f:
        for row in csv.DictReader(f):
            doc_id = Path(row.get("original_filename") or "").stem
            if doc_id:
                m[doc_id] = row.get("text") or ""
    return m


def main():
    tmap = text_map()
    gt_all = json.loads((RES / "ground_truth_realkie_fcc.json").read_text())
    res_all = json.loads((RES / "extraction_results_realkie_fcc.json").read_text())
    ext = next(iter(next(iter(res_all.values())).keys()))

    records, meta = [], {}
    skipped = dropped = 0
    for doc_id, blob in res_all.items():
        pred = (blob.get(ext, {}).get("extracted")) or {}
        if blob.get(ext, {}).get("metrics", {}).get("error") or not pred:
            skipped += 1; continue
        text = tmap.get(doc_id, "")
        if not text:
            skipped += 1; continue
        gt = gt_all.get(doc_id, {})
        ner, entities, mfields = {}, [], {}
        fields = set(pred) | set(gt)
        for f in sorted(fields):
            pv = pred.get(f)
            status, gt_str = membership(pv, gt.get(f))
            if status is None:          # unlabelled (GT-absent, pred-present): drop from train+eval
                dropped += 1; continue
            ner[f] = "" if pv is None else str(pv)
            entities.append({"fieldName": f, "groundTruth": gt_str})
            mfields[f] = {"pred": pv, "gt": gt.get(f),
                          "field_type": "lineitem" if f.lower().startswith("line item") else "scalar",
                          "member_correct": status}
        records.append({"documentId": doc_id, "text": text, "NER_Output": ner, "entities": entities})
        meta[doc_id] = mfields

    # 80/20 doc split
    ids = sorted(meta)
    rng = random.Random(SEED); rng.shuffle(ids)
    n_tr = round(TRAIN_FRAC * len(ids))
    train_ids, test_ids = set(ids[:n_tr]), set(ids[n_tr:])
    tr = [r for r in records if r["documentId"] in train_ids]
    te = [r for r in records if r["documentId"] in test_ids]

    (OUT / "train").mkdir(parents=True, exist_ok=True)
    (OUT / "test").mkdir(parents=True, exist_ok=True)
    (OUT / "meta").mkdir(parents=True, exist_ok=True)
    (OUT / "train" / f"{DOC_TYPE}.json").write_text(json.dumps(tr))
    (OUT / "test" / f"{DOC_TYPE}.json").write_text(json.dumps(te))
    (OUT / "meta" / "train_meta.json").write_text(json.dumps({d: meta[d] for d in train_ids}))
    (OUT / "meta" / "test_meta.json").write_text(json.dumps({d: meta[d] for d in test_ids}))
    (OUT / "split.json").write_text(json.dumps(
        {"seed": SEED, "train_frac": TRAIN_FRAC, "n_docs": len(records),
         "n_train": len(tr), "n_test": len(te), "skipped": skipped, "dropped_unlabelled": dropped,
         "train_ids": sorted(train_ids), "test_ids": sorted(test_ids)}, indent=2))

    n_fields = sum(len(m) for m in meta.values())
    n_scalar = sum(1 for m in meta.values() for v in m.values() if v["field_type"] == "scalar")
    print(f"docs: {len(records)} (skipped {skipped})  train {len(tr)} / test {len(te)}")
    print(f"field instances: {n_fields}  (scalar {n_scalar}, lineitem {n_fields-n_scalar})  dropped_unlabelled={dropped}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
