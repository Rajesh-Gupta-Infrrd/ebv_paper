#!/usr/bin/env python3
"""
Run the trained Signal verifier on held-out FCC TEST docs via dociq's NTPInferenceEngine
(imported in place; dociq untouched). Capture per (doc,field): production decision
(binary accept=NTP/route=REVIEW, and 3-tier), final_score, all signals, empty-prior
provenance, AND the best-model predict_proba (features built in the model's feature order).

Usage: infer_signal.py [--bundle DIR] [--out FILE]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import joblib
import pandas as pd

EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
UNS = EBV / "experiments" / "unstructured_ntp"
DOCIQ_NTP = "/Users/rajeshgupta/Git_Clones/dociq/app/ntp_classifier"
sys.path.insert(0, DOCIQ_NTP)
from ntp_inference import NTPInferenceEngine  # noqa: E402

TEST = json.loads((UNS / "realkie_fcc" / "data" / "test" / "invoice.json").read_text())
META = json.loads((UNS / "realkie_fcc" / "data" / "meta" / "test_meta.json").read_text())


def _sig_val(v):
    if v is None:
        return -1.0
    if isinstance(v, bool):
        return 0.0 if v is False else -1.0
    try:
        return float(v)
    except Exception:
        return -1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default=str(UNS / "realkie_fcc" / "bundle"))
    ap.add_argument("--out", default=str(UNS / "realkie_fcc" / "decisions" / "fcc_decisions.jsonl"))
    a = ap.parse_args()
    bundle = Path(a.bundle)
    if not bundle.is_absolute():
        bundle = UNS / bundle

    model = joblib.load(bundle / "models" / "best_model_invoice.joblib")
    feats = list(model.feature_names_in_)
    prior_raw = json.loads((bundle / "field_gt_empty_prior.json").read_text())
    prior = prior_raw.get("invoice", prior_raw) if isinstance(prior_raw, dict) else {}
    pos = list(model.classes_).index(1) if 1 in list(getattr(model, "classes_", [1])) else 1

    def proba(signals, field, value):
        try:
            is_empty = 1.0 if (value is None or str(value).strip() == "") else 0.0
            ger = prior.get(field, {}).get("gt_empty_rate", -1.0)
            rowv = {}
            for name in feats:
                if name == "is_empty":
                    rowv[name] = is_empty
                elif name == "gt_empty_rate":
                    rowv[name] = float(ger) if ger is not None else -1.0
                else:
                    rowv[name] = _sig_val((signals or {}).get(name))
            return float(model.predict_proba(pd.DataFrame([rowv], columns=feats))[0, pos])
        except Exception:
            return None

    engine = NTPInferenceEngine(model_dir=str(bundle / "models"), config_dir=str(bundle))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out = open(a.out, "w")
    n = 0
    for rec in TEST:
        doc = rec["documentId"]; ner = rec["NER_Output"]; text = rec["text"]
        rb = engine.predict_document(ner, text, "invoice", mode="binary")
        try:
            r3 = engine.predict_document(ner, text, "invoice", mode="3tier")
        except Exception:
            r3 = {"fields": {}}
        for f, fr in rb.get("fields", {}).items():
            m = META.get(doc, {}).get(f, {})
            dec_bin = fr.get("decision")
            dec_3t = r3.get("fields", {}).get(f, {}).get("decision")
            out.write(json.dumps({
                "doc": doc, "field": f, "field_type": m.get("field_type"),
                "correct": m.get("member_correct"),
                "decision_bin": dec_bin, "accept_bin": dec_bin == "NTP",
                "decision_3t": dec_3t, "accept_3t": dec_3t == "NTP",
                "final_score": fr.get("final_score"),
                "proba": proba(fr.get("signals"), f, fr.get("value", ner.get(f))),
                "gt_empty_rate": fr.get("gt_empty_rate"),
                "empty_prior_applied": fr.get("empty_prior_applied"),
                "gated": fr.get("gated"), "signals": fr.get("signals"),
            }, default=str) + "\n")
            n += 1
    out.close()
    print(f"scored {n} field decisions over {len(TEST)} test docs (bundle={bundle.name}) -> {a.out}")


if __name__ == "__main__":
    main()
