"""Recompute the Signal frontier split into: value-verification blind spot (confidently-wrong on
NON-EMPTY predictions = wrong value the verifier accepts) vs extractor-empty misses (pred empty,
GT present = extractor recall failure, not a value-verification blind spot). Joins decisions->data."""
import json, os
U = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/unstructured_ntp"
DOMS = {
    "FCC":       (f"{U}/realkie_fcc/decisions/fcc_decisions_clean.jsonl",       f"{U}/realkie_fcc/data/test/invoice.json"),
    "S1":        (f"{U}/realkie_s1/decisions/realkie_s1_clean.jsonl",            f"{U}/realkie_s1/data_clean/test/s1_filing.json"),
    "Charities": (f"{U}/realkie_charities/decisions/realkie_charities_clean.jsonl", f"{U}/realkie_charities/data_clean/test/charity_report.json"),
}
def pred_lookup(datafile):
    d = json.load(open(datafile)); out = {}
    for rec in d:
        out[rec["documentId"]] = rec.get("NER_Output") or {}
    return out
def is_empty(v): return v is None or str(v).strip() == ""

summary = {}
pooled = {"ne_err": 0, "ne_cw": 0, "emptymiss": 0, "all_err": 0}
for name, (decf, dataf) in DOMS.items():
    dec = [json.loads(l) for l in open(decf)]
    dec = [o for o in dec if o.get("field_type") == "scalar"]
    pl = pred_lookup(dataf)
    cors = sorted(o["proba"] for o in dec if o["correct"] and o.get("proba") is not None)
    med = cors[len(cors) // 2]
    errs = [o for o in dec if not o["correct"]]
    cw = [o for o in errs if o.get("accept_3t") and o.get("proba") is not None and o["proba"] >= med]
    def getpred(o): return (pl.get(o["doc"]) or {}).get(o["field"])
    ne_err = [o for o in errs if not is_empty(getpred(o))]            # errors where extractor produced a value
    ne_cw = [o for o in cw if not is_empty(getpred(o))]              # value-verification blind spot
    empty_cw = [o for o in cw if is_empty(getpred(o))]              # extractor-empty misses
    vf = len(ne_cw) / max(len(ne_err), 1)
    summary[name] = {"n_errors": len(errs), "n_errors_nonempty": len(ne_err),
                     "confidently_wrong_total": len(cw),
                     "value_blindspot_nonempty": len(ne_cw), "extractor_empty_misses": len(empty_cw),
                     "VALUE_FRONTIER_nonempty": round(vf, 3),
                     "old_frontier_all": round(len(cw) / max(len(errs), 1), 3)}
    pooled["ne_err"] += len(ne_err); pooled["ne_cw"] += len(ne_cw); pooled["emptymiss"] += len(empty_cw); pooled["all_err"] += len(errs)
    print(f"{name:10s} errors={len(errs):4d} (non-empty {len(ne_err):4d})  confidently-wrong={len(cw):3d} "
          f"-> value-blindspot(non-empty)={len(ne_cw):3d}  extractor-empty-miss={len(empty_cw):3d}  "
          f"VALUE-FRONTIER={vf:.3f}  (old all-errors frontier={len(cw)/max(len(errs),1):.3f})")
pv = pooled["ne_cw"] / max(pooled["ne_err"], 1)
print(f"\nPOOLED(FCC+S1+Char): value-frontier(non-empty)={pv:.3f} ({pooled['ne_cw']}/{pooled['ne_err']})  "
      f"extractor-empty-misses={pooled['emptymiss']}")
summary["POOLED"] = {"value_frontier_nonempty": round(pv, 3), "value_blindspot": pooled["ne_cw"],
                     "errors_nonempty": pooled["ne_err"], "extractor_empty_misses": pooled["emptymiss"]}
json.dump(summary, open(f"{os.path.dirname(__file__)}/../analysis/frontier_nonempty.json", "w"), indent=1)
print("saved -> analysis/frontier_nonempty.json")
