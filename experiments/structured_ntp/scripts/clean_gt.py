#!/usr/bin/env python3
"""
TASK 2: Clean FATURA ground truth to pure values, then validate it's good enough
to run NTP end-to-end with EXACT matching.

FATURA GT bundles label+value+unit (e.g. DATE="Date: 20-Mar-2008",
TOTAL="TOTAL : 734.33 EUR"). NTP's field-aware matcher does NOT strip labels but
DOES handle units/number-formats/dates numerically. So cleaning = strip the label
prefix (up to and including the LAST colon); leave the rest to NTP's matcher.

Validation: compare clean-GT vs NuExtract predictions with NTP's OWN field-aware
matcher (exact path), and against the earlier containment labels. High agreement =>
cleaning is trustworthy for an exact-match end-to-end run.

Writes:
  gt_clean/ground_truth_fatura_clean.json
  gt_clean/cleaning_quality.json   (per-field + overall match/agreement + examples)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NTP_DIR = "/Users/rajeshgupta/Git_Clones/NTP/NTP"
sys.path.insert(0, NTP_DIR)
from compute_roi import values_match_field_aware  # noqa: E402  (NTP's field-aware matcher)

EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
RES = EBV / "experiments" / "results" / "fatura_results"
OUT = EBV / "experiments" / "structured_ntp/fatura" / "gt_clean"

_ALNUM = re.compile(r"[^a-z0-9]+")

# FATURA field-type groups (labels/separators differ by type, so cleaning must too).
AMOUNT_FIELDS = {"TOTAL", "SUB_TOTAL", "TAX", "DISCOUNT", "AMOUNT_DUE"}
ID_LABEL_RE = re.compile(r"^\s*(invoice\s*(number|no\.?|#)?|number|no\.?|gstin|po\s*number)\s*[:#]?\s*",
                         re.IGNORECASE)


def clean_value(v, field: str = ""):
    """Strip the FATURA label to recover the pure value. Field-type-aware:
       - AMOUNT: drop parenthetical (x%) and keep the numeric value (magnitude).
       - everything else: strip the leading label up to its first ':' or '#'
         (keeps multi-line block values whose internals contain colons), with an
         extra pass for id-style labels ('INVOICE #', 'Invoice number')."""
    if v is None:
        return None
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = re.sub(r"\s+", " ", s.replace("\n", " ")).strip()
    s = s.replace("- ", "")  # fix OCR line-break hyphenation ("sevent- y-seven")

    base = (field or "").upper()
    if base in AMOUNT_FIELDS:
        s2 = re.sub(r"\([^)]*\)", "", s)                    # drop "(1.85%)" etc.
        nums = re.findall(r"\d[\d,]*\.?\d*", s2)             # magnitude(s)
        return (nums[-1].replace(",", "") if nums else (s or None))

    # strip leading label up to the FIRST ':' or '#' that sits in the leading region
    m = re.search(r"[:#]", s[:40])
    if m:
        s = s[m.start() + 1:].strip()
    else:
        s = ID_LABEL_RE.sub("", s).strip()                  # 'Invoice number 2Y..' -> '2Y..'
    return s or None


def ntp_match(gt, pred, field):
    try:
        return bool(values_match_field_aware(gt, pred, field))
    except TypeError:
        return bool(values_match_field_aware(gt, pred))


def contain_match(pred, gt):
    p = _ALNUM.sub("", (pred or "").lower())
    g = _ALNUM.sub("", (gt or "").lower())
    if not p or not g:
        return False
    return p == g if len(p) < 2 else (p in g or g in p)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gt_all = json.loads((RES / "ground_truth_fatura.json").read_text())
    res_all = json.loads((RES / "extraction_results_fatura.json").read_text())
    extractor = next(iter(next(iter(res_all.values())).keys()))

    # 1) clean
    clean = {d: {f: clean_value(v, f) for f, v in fields.items()} for d, fields in gt_all.items()}
    (OUT / "ground_truth_fatura_clean.json").write_text(json.dumps(clean))

    # 2) validate: present-field non-null predictions
    from collections import defaultdict
    per_field = defaultdict(lambda: {"n": 0, "ntp_exact": 0, "containment": 0, "agree": 0})
    disagree_examples = []
    n = ntp_ok = cont_ok = agree = 0
    for d, pred_blob in res_all.items():
        pred = (pred_blob.get(extractor, {}).get("extracted")) or {}
        for f, pv in pred.items():
            if pv is None:
                continue
            cg = clean[d].get(f)
            if cg is None:
                continue  # field absent in GT -> not in present-field population
            e = ntp_match(cg, str(pv), f)
            c = contain_match(str(pv), cg)
            n += 1; ntp_ok += e; cont_ok += c; agree += (e == c)
            s = per_field[f]
            s["n"] += 1; s["ntp_exact"] += e; s["containment"] += c; s["agree"] += (e == c)
            if e != c and len(disagree_examples) < 40:
                disagree_examples.append({"field": f, "pred": str(pv)[:40],
                                          "clean_gt": str(cg)[:40], "ntp_exact": e, "containment": c})

    quality = {
        "present_field_preds": n,
        "ntp_exact_match_rate": round(ntp_ok / n, 4) if n else None,
        "containment_match_rate": round(cont_ok / n, 4) if n else None,
        "exact_vs_containment_agreement": round(agree / n, 4) if n else None,
        "per_field": {f: {**s,
                          "ntp_exact_rate": round(s["ntp_exact"] / s["n"], 3),
                          "agree_rate": round(s["agree"] / s["n"], 3)}
                      for f, s in sorted(per_field.items(), key=lambda kv: -kv[1]["n"])},
        "disagreement_examples": disagree_examples,
    }
    (OUT / "cleaning_quality.json").write_text(json.dumps(quality, indent=2))
    print(f"cleaned GT -> {OUT/'ground_truth_fatura_clean.json'}")
    print(f"present-field non-null preds: {n}")
    print(f"NTP exact-match rate (clean GT vs pred): {quality['ntp_exact_match_rate']}")
    print(f"containment-match rate:                  {quality['containment_match_rate']}")
    print(f"exact vs containment AGREEMENT:          {quality['exact_vs_containment_agreement']}")
    print("sample disagreements:")
    for ex in disagree_examples[:12]:
        print(f"  {ex['field']:16} pred={ex['pred']!r:30} clean_gt={ex['clean_gt']!r:30} "
              f"exact={ex['ntp_exact']} contain={ex['containment']}")


if __name__ == "__main__":
    main()
