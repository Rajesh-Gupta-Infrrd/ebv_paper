"""E3b for Signal — natural-error atlas: label every scalar ERROR by failure family (rule-based,
from pred/GT/source-text that are already available), then the H2 detectability map (per family,
caught@deployed + which signal discriminates). Completes the Signal side of E3b (was deferred)."""
import json, re, numpy as np, os
U = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/unstructured_ntp"
DOMS = {"FCC": (f"{U}/realkie_fcc/decisions/fcc_decisions_clean.jsonl", f"{U}/realkie_fcc/data/test/invoice.json"),
        "S1": (f"{U}/realkie_s1/decisions/realkie_s1_clean.jsonl", f"{U}/realkie_s1/data_clean/test/s1_filing.json"),
        "Charities": (f"{U}/realkie_charities/decisions/realkie_charities_clean.jsonl", f"{U}/realkie_charities/data_clean/test/charity_report.json")}
AL = re.compile(r"[^a-z0-9]+")
def norm(x): return AL.sub("", str(x).lower()) if x is not None else ""
def family(pred, gt, text, other_gt_vals):
    """Failure family of a wrong extraction (order matters; matched against other fields' GT)."""
    p, g, t = norm(pred), norm(gt), norm(text)
    if p == "":                       return "missing"               # extractor emitted nothing
    if t and p not in t:              return "source_absent"         # value not in the document (hallucination)
    # pred IS in the document but wrong. Is it another field's GT value? -> cross-field copy
    for v in other_gt_vals:
        if v and len(norm(v)) > 3 and norm(v) == p and norm(v) != g:
            return "cross_field_copy"
    return "wrong_value_in_source"    # a real value from the doc, but the wrong one for this field

rows_all = []
for name, (decf, dataf) in DOMS.items():
    dec = [json.loads(l) for l in open(decf)]; dec = [o for o in dec if o.get("field_type") == "scalar"]
    data = {d["documentId"]: d for d in json.load(open(dataf))}
    cors = sorted(o["proba"] for o in dec if o["correct"] and o.get("proba") is not None); med = cors[len(cors)//2]
    for o in dec:
        if o["correct"]: continue
        d = data.get(o["doc"], {}); ner = d.get("NER_Output") or {}
        pred = ner.get(o["field"]); text = d.get("text", "")
        ents = {e["fieldName"]: e.get("groundTruth") for e in d.get("entities", [])}
        gt = ents.get(o["field"])
        other_gt = [v for f, v in ents.items() if f != o["field"]]   # other fields' GT values
        fam = family(pred, gt, text, other_gt)
        caught = not bool(o.get("accept_3t"))            # caught = rejected at deployed threshold
        rows_all.append({"domain": name, "field": o["field"], "family": fam, "caught": caught,
                         "proba": o.get("proba"), "accepted": bool(o.get("accept_3t"))})

from collections import Counter, defaultdict
fam_count = Counter(r["family"] for r in rows_all)
print(f"=== Signal natural-error atlas (n_errors={len(rows_all)}) — family distribution ===")
for f, c in fam_count.most_common(): print(f"  {f:22s} {c}")
print("\n=== H2 detectability map: per family, caught@deployed (reject rate) ===")
famstats = {}
for f in fam_count:
    sub = [r for r in rows_all if r["family"] == f]
    cr = sum(1 for r in sub if r["caught"]) / len(sub)
    famstats[f] = {"n": len(sub), "caught_at_deployed": round(cr, 3)}
    print(f"  {f:22s} n={len(sub):4d}  caught@deployed={cr:.3f}")
out = {"n_errors": len(rows_all), "family_distribution": dict(fam_count),
       "detectability_map": famstats,
       "note": "families assigned by rule from pred/GT/source-text (no re-extraction). caught=rejected at accept_3t."}
json.dump(out, open(f"{os.path.dirname(__file__)}/../analysis/signal_atlas.json", "w"), indent=1)
print("\nsaved -> analysis/signal_atlas.json")
