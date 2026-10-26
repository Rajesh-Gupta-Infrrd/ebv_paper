#!/usr/bin/env python3
"""Evidence for the GT-sparsity cleanup: WHY is GT empty for some fields?
For every (doc, field) where GT is empty but the model predicted a value, check whether that
predicted value actually appears in the document's own text. If it does, the empty GT is an
ANNOTATION GAP (value present, label missing) — not genuine field absence — which justifies the
`clean` labeling (drop as unverifiable) over `noisy` (label 'wrong'). Runs on all Signal domains.
No model call. Writes analysis/annotation_gap.json + prints the table."""
import json, csv, sys, re
from pathlib import Path
csv.field_size_limit(sys.maxsize)
EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
EXP = EBV / "experiments"
AL = re.compile(r"[^a-z0-9]+")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
def norm(x): return AL.sub("", str(x).lower()) if x is not None else ""

# (label, results-dir, results-file-stem, csv-dir, key-mode)
DOMAINS = [
    ("Charities", "realkie_charities_results", "realkie_charities", "realkie_charities", "uuid"),
    ("FCC",       "realkie_fcc_results",       "realkie_fcc",       "realkie_fcc_invoices", "uuid"),
    ("S-1",       "realkie_s1_results",        "realkie_s1",        "realkie_s1",         "stem"),
]


def present(v):
    xs = v if isinstance(v, list) else [v]
    return any(x is not None and str(x).strip() not in ("", "None") for x in xs)


def build_text_map(csv_dir, key_mode):
    tmap = {}
    with open(EBV / csv_dir / "train.csv") as f:
        for row in csv.DictReader(f):
            of = row.get("original_filename") or ""
            if key_mode == "uuid":
                m = UUID.search(of)
                if m: tmap.setdefault(m.group(0), []).append(row.get("text") or "")
            else:  # stem = filename without .pdf (S-1 page rows share it)
                stem = of.rsplit(".pdf", 1)[0]
                if stem: tmap.setdefault(stem, []).append(row.get("text") or "")
    return tmap


def doc_key(doc, key_mode):
    if key_mode == "uuid":
        m = UUID.search(doc); return m.group(0) if m else None
    return doc.split("__")[0]


def analyze(label, resdir, stem, csvdir, key_mode):
    rp = EXP / "results" / resdir
    R = json.loads((rp / f"extraction_results_{stem}.json").read_text())
    G = json.loads((rp / f"ground_truth_{stem}.json").read_text())
    exk = next(iter(next(iter(R.values())).keys()))
    tmap = build_text_map(csvdir, key_mode)
    in_t = nin = notx = 0; degen = 0
    for doc, md in R.items():
        txt = " ".join(tmap.get(doc_key(doc, key_mode) or "", []))
        ext = (md.get(exk, {}).get("extracted") or {}); gt = G.get(doc, {})
        for fld, p in ext.items():
            ps = str(p).strip()
            if p is None or ps == "": continue
            if fld in gt and present(gt[fld]): continue      # GT-empty only
            if ps in ("[]", "{}") or re.fullmatch(r"[\[\(]?[\s●•\-–—,]*[\]\)]?", ps):
                degen += 1; continue                          # degenerate/placeholder output
            if not txt: notx += 1; continue
            np = norm(p)[:40]
            if np and np in norm(txt): in_t += 1
            else: nin += 1
    tot = in_t + nin
    return {"label": label, "gt_empty_pred_present": tot + degen, "scored": tot, "degenerate": degen,
            "in_text": in_t, "not_in_text": nin, "no_text": notx,
            "in_text_pct": round(in_t / tot * 100, 1) if tot else None}


def main():
    out = [analyze(*d) for d in DOMAINS]
    print(f"{'domain':10} {'GT-empty+pred':>13} {'degen':>6} {'scored':>7} {'in-text%':>9} {'not-in-text':>11}")
    for r in out:
        print(f"{r['label']:10} {r['gt_empty_pred_present']:>13} {r['degenerate']:>6} {r['scored']:>7} "
              f"{str(r['in_text_pct'])+'%':>9} {r['not_in_text']:>11}")
    (EXP / "unstructured_ntp" / "analysis" / "annotation_gap.json").write_text(json.dumps(out, indent=2))
    print(f"\n-> {EXP/'unstructured_ntp'/'analysis'/'annotation_gap.json'}")


if __name__ == "__main__":
    main()
