import json, numpy as np
from sklearn.metrics import roc_auc_score, cohen_kappa_score
SC = "/private/tmp/claude-505/-Users-rajeshgupta-Projects-DocAI/dcbf7cdb-afa7-4247-b410-36141681f0c1/scratchpad/rocket_cd_tables"
man = {str(x["i"]): x for x in json.load(open(f"{SC}/manifest.json"))}
A = json.load(open(f"{SC}/labels_A.json"))
B = json.load(open(f"{SC}/labels_B.json"))

def lab(d, k): return (d.get(k) or {}).get("label", "").upper()
keys = [k for k in man if man[k]["trust"] is not None and k in A and k in B]
la = [lab(A, k) for k in keys]; lb = [lab(B, k) for k in keys]
kappa = cohen_kappa_score(la, lb)
agree = [k for k in keys if lab(A, k) == lab(B, k)]
disagree = [k for k in keys if lab(A, k) != lab(B, k)]
print(f"n={len(keys)}  annotator agreement={len(agree)}/{len(keys)} ({len(agree)/len(keys)*100:.0f}%)  Cohen kappa={kappa:.2f}")
print(f"disagreements (need adjudication): {len(disagree)} -> indices {disagree}")

# GT from agreement; disagreements left out of the primary metric (or adjudicate manually)
gt = {k: (lab(A, k) == "GOOD") for k in agree}   # True=GOOD
trust = np.array([man[k]["trust"] for k in agree])
good = np.array([gt[k] for k in agree])
nbad = int((~good).sum())
print(f"\nGT (agreed set): n={len(agree)}  GOOD={int(good.sum())}  BAD={nbad}")
if len(set(good.tolist())) > 1 and nbad >= 3:
    auc = roc_auc_score(good, trust)                      # trust predicts GOOD
    # bad-catch @ trust<85 (reject), precision-first
    rej = trust < 85
    bad_catch = (~good & rej).sum() / max(1, nbad)
    false_rej = (good & rej).sum() / max(1, int(good.sum()))
    print(f"AUROC(trust vs GOOD) = {auc:.3f}")
    print(f"bad-catch @ trust<85 = {bad_catch:.3f}  ({(~good & rej).sum()}/{nbad})   false-reject = {false_rej:.3f}")
else:
    print("too few BAD in agreed set for AUROC/bad-catch")
json.dump({"n": len(keys), "kappa": round(float(kappa),3), "agreement": len(agree)/len(keys),
           "disagree_idx": disagree}, open(f"{SC}/gt_reconcile.json", "w"), indent=1)
