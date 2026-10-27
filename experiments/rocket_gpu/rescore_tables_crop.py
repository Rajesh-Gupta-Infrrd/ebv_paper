import sys, json
sys.path.insert(0, "/Users/rajeshgupta/Projects/DocAI")
sys.path.insert(0, "/Users/rajeshgupta/Projects/DocAI/scripts/extract/table_extractor")
from scripts.extract.table_extractor.scoring import score_table_trust
import numpy as np
from sklearn.metrics import roc_auc_score

SC = "/private/tmp/claude-505/-Users-rajeshgupta-Projects-DocAI/dcbf7cdb-afa7-4247-b410-36141681f0c1/scratchpad/rocket_cd_tables"
man = json.load(open(f"{SC}/manifest.json"))
BAD = {"1", "14", "22", "33"}   # finalized GT (2-annotator + adjudication)

out = []
for x in man:
    i = str(x["i"]); crop = x["crop"]; html = x["html"]
    try:
        # witness = docTR on the TABLE CROP only (not the full page) -> fair text-conservation
        res = score_table_trust(table_html=html, image_path=crop, run_doctr_if_needed=True)
        tc = res.signals.get("text_conservation")
        recall = tc.details.get("recall") if tc else None
        out.append({"i": i, "trust_old": x["trust"], "trust_new": round(float(res.base_trust_score), 1),
                    "recall": round(recall, 2) if recall is not None else None})
    except Exception as e:
        out.append({"i": i, "trust_old": x["trust"], "trust_new": None, "err": str(e)[:60]})
json.dump(out, open(f"{SC}/rescore_crop.json", "w"), indent=1)

ok = [r for r in out if r["trust_new"] is not None]
keys = [r["i"] for r in ok]
trust = np.array([r["trust_new"] for r in ok])
good = np.array([k not in BAD for k in keys])
nbad = int((~good).sum())
print(f"n={len(ok)}  GOOD={int(good.sum())}  BAD={nbad}")
print(f"median recall (witness quality): old-run was ~0.25 -> new crop-run median recall = {np.median([r['recall'] for r in ok if r['recall'] is not None]):.2f}")
auc = roc_auc_score(good, trust)
rej = trust < 85
print(f"NEW trust: median={np.median(trust):.0f}  >=85={int((trust>=85).sum())}  <85={int((trust<85).sum())}")
print(f"AUROC(trust vs GOOD) = {auc:.3f}")
print(f"bad-catch @ trust<85 = {(~good & rej).sum()}/{nbad} = {(~good&rej).sum()/nbad:.2f}   false-reject = {(good&rej).sum()}/{int(good.sum())} = {(good&rej).sum()/int(good.sum()):.2f}")
print("BAD tables new trust:", {k: t for k, t, g in zip(keys, trust, good) if not g})
