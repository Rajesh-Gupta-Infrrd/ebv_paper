"""Re-emit RD Table-Trust per-channel signals on the clear cases (reconciled to review_data trust),
to get a RELIABLE structural-only vs witness-only number (218 BAD + 69 GOOD, not ParseBench's n=6).
Replicates evaluate_rdbench_trust.py's exact call: table_html=actual_html, image_path, ocr_result
from the pred file, run_doctr_if_needed. Probes both docTR settings to match review_data trust first."""
import json, os, sys, argparse
sys.path.insert(0, "/Users/rajeshgupta/Projects/DocAI")
from scripts.extract.table_extractor.scoring import score_table_trust
DOCAI = "/Users/rajeshgupta/Projects/DocAI"
RD = f"{DOCAI}/eval/table_extraction/rdbench"
OUT = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/indirect/analysis/rd_signals.json"

def jsonify(x):
    if isinstance(x, dict): return {k: jsonify(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [jsonify(v) for v in x]
    if isinstance(x, (bool, int, float, str)) or x is None: return x
    if hasattr(x, "item"):
        try: return x.item()
        except Exception: pass
    if hasattr(x, "__dict__"): return jsonify(vars(x))
    return str(x)

ap = argparse.ArgumentParser(); ap.add_argument("--probe", action="store_true"); a = ap.parse_args()
rev = json.load(open(f"{RD}/table_trust_eval/review_data.json"))
clear = [r for r in rev if r["cls"] != "HDR"]
byid = {r["full_id"]: r for r in clear}

def score_one(fid, with_doctr):
    p = f"{RD}/outputs/mineru/{fid}.json"
    if not os.path.exists(p): return None
    pr = json.load(open(p))
    html = pr.get("actual_html") or ""
    img = f"{DOCAI}/{byid[fid]['img']}"
    ocr = pr.get("ocr_result") if isinstance(pr.get("ocr_result"), dict) else None
    res = score_table_trust(table_html=html, image_path=img if os.path.exists(img) else None,
                            ocr_result=ocr, run_doctr_if_needed=with_doctr)
    return res

if a.probe:
    print("probe: trust_new vs review_data trust (5 cases) @ with_doctr True/False")
    for fid in list(byid)[:5]:
        tgt = byid[fid]["trust"]
        for wd in (True, False):
            res = score_one(fid, wd)
            t = getattr(res, "base_trust_score", None)
            print(f"  {byid[fid]['case_id']:10s} target={tgt:6.2f}  with_doctr={wd} -> {t}")
    sys.exit(0)

# full run (pick with_doctr based on probe; default True)
WD = True
man = []
for i, fid in enumerate(byid):
    r = byid[fid]
    res = score_one(fid, WD)
    if res is None: continue
    sg = getattr(res, "signals", None)
    man.append({"case_id": r["case_id"], "full_id": fid, "gt": r["gt"], "defect": r["defect"],
                "trust_target": r["trust"], "trust_new": jsonify(getattr(res, "base_trust_score", None)),
                "signals": jsonify(sg), "codes": jsonify(getattr(res, "reason_codes", None))})
    if (i + 1) % 25 == 0: print(f"scored {i+1}", file=sys.stderr)
json.dump(man, open(OUT, "w"), indent=1, default=str)
print(f"wrote {len(man)} -> {OUT}", file=sys.stderr)
