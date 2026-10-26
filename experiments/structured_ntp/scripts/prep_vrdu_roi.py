#!/usr/bin/env python3
"""
Prepare VRDU (registration-form / FARA) for the structured ROI matrix so it slots into
the SAME run_matrix.py pipeline used for FATURA. Produces, from dataset.jsonl only
(no page images needed — ROI works on OCR token coordinates):

  1. splits/vrdu_split.json      per-template 70/30 (seed 42). Template is recovered from
                                 the filename's last '_'-delimited component (Short-Form /
                                 Amendment / Dissemination Report) — VRDU's 3 form types.
  2. inputs/vrdu_ocr/<docId>.json   FATURA-style flat token list, coords in 0-1000 space,
                                 page_number = 0-based page +1 (NTP rejects page_number<=0).
  3. gt_clean/ground_truth_vrdu_clean.json  whitespace-stripped GT (VRDU GT is already clean
                                 values; clean == strip trailing '\\n'). Needed because
                                 run_matrix.py reads a *_clean.json alongside the raw GT.

Usage: prep_vrdu_roi.py   (idempotent; overwrites its outputs)
"""
from __future__ import annotations
import json, random
from pathlib import Path

SEED, TRAIN_FRAC = 42, 0.70
EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
EXP = EBV / "experiments"
JSONL = EBV / "experiments" / "datasets" / "vrdu" / "registration-form" / "main" / "dataset.jsonl"
OCR_OUT = EXP / "structured_ntp" / "inputs" / "vrdu_ocr"
SPLIT_OUT = EXP / "structured_ntp" / "splits" / "vrdu_split.json"
CLEAN_OUT = EXP / "structured_ntp/vrdu" / "gt_clean" / "ground_truth_vrdu_clean.json"
RES_DIR = EXP / "results" / "vrdu_results"


def template_of(filename: str) -> str:
    """VRDU form type = last '_'-delimited component of the filename stem."""
    return Path(filename).stem.rsplit("_", 1)[-1]


def entries():
    with open(JSONL) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except Exception:
                    continue


def ocr_tokens(e) -> list[dict]:
    """dataset.jsonl ocr.pages[].tokens -> FATURA-style flat tokens (0-1000, page_number>=1)."""
    out, i = [], 0
    for page in (e.get("ocr", {}) or {}).get("pages", []) or []:
        for t in page.get("tokens", []) or []:
            bb = t.get("bbox") or []
            if len(bb) < 5:
                continue
            pg, x0, y0, x1, y1 = bb[0], bb[1], bb[2], bb[3], bb[4]
            txt = str(t.get("text", "")).strip()
            if not txt:
                continue
            out.append({
                "id": f"token_{int(pg)+1}_{i}",
                "text": txt,
                "startX": round(x0 * 1000), "startY": round(y0 * 1000),
                "endX": round(x1 * 1000), "endY": round(y1 * 1000),
                "page_number": int(pg) + 1,          # 0-based -> 1-based (NTP requires >0)
                "startIndex": i,
            })
            i += 1
    return out


def strip_gt(v):
    if v is None:
        return None
    if isinstance(v, list):
        out = [str(x).strip() for x in v if x is not None and str(x).strip()]
        return out or None
    s = str(v).strip()
    return s or None


def main():
    OCR_OUT.mkdir(parents=True, exist_ok=True)
    SPLIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    CLEAN_OUT.parent.mkdir(parents=True, exist_ok=True)

    by_tmpl: dict[str, list[str]] = {}
    n_ocr = n_tokens = 0
    for e in entries():
        fn = e.get("filename") or ""
        if not fn:
            continue
        doc_id = Path(fn).stem
        by_tmpl.setdefault(template_of(fn), []).append(doc_id)
        toks = ocr_tokens(e)
        (OCR_OUT / f"{doc_id}.json").write_text(json.dumps(toks))
        n_ocr += 1; n_tokens += len(toks)

    # per-template 70/30 split (seed 42), same schema as fatura_split.json
    per_template = {}
    for tmpl, ids in by_tmpl.items():
        ids = sorted(ids)
        rng = random.Random(SEED); rng.shuffle(ids)
        k = round(TRAIN_FRAC * len(ids))
        per_template[tmpl] = {"train": sorted(ids[:k]), "test": sorted(ids[k:])}
    SPLIT_OUT.write_text(json.dumps(
        {"seed": SEED, "train_frac": TRAIN_FRAC, "per_template": per_template}, indent=2))

    # clean GT = whitespace-stripped raw GT
    raw = json.loads((RES_DIR / "ground_truth_vrdu.json").read_text())
    clean = {d: {f: strip_gt(v) for f, v in (fields or {}).items()} for d, fields in raw.items()}
    CLEAN_OUT.write_text(json.dumps(clean))

    print(f"templates: " + ", ".join(f"{t}={len(v)}" for t, v in sorted(by_tmpl.items())))
    print(f"split -> {SPLIT_OUT}  ({sum(len(v['train']) for v in per_template.values())} train / "
          f"{sum(len(v['test']) for v in per_template.values())} test)")
    print(f"ocr   -> {OCR_OUT}  ({n_ocr} docs, {n_tokens} tokens, avg {n_tokens//max(n_ocr,1)}/doc)")
    print(f"clean -> {CLEAN_OUT}  ({len(clean)} docs)")


if __name__ == "__main__":
    main()
