import json, numpy as np
from sklearn.metrics import roc_auc_score, cohen_kappa_score
SC = "/private/tmp/claude-505/-Users-rajeshgupta-Projects-DocAI/dcbf7cdb-afa7-4247-b410-36141681f0c1/scratchpad/rocket_other_tables"
# trust per key
trust = {}
for typ in ["Bank", "CreditReportLender"]:
    for x in json.load(open(f"{SC}/{typ}_manifest.json")):
        trust[f"{typ}_{x['i']}"] = x["trust"]
A = json.load(open(f"{SC}/labels_A.json")); B = json.load(open(f"{SC}/labels_B.json"))
def lab(d, k): return (d.get(k) or {}).get("label", "").upper()
keys = [k for k in A if k in B and trust.get(k) is not None]
la = [lab(A, k) for k in keys]; lb = [lab(B, k) for k in keys]
kappa = cohen_kappa_score(la, lb)
agree = [k for k in keys if lab(A, k) == lab(B, k)]
disagree = [k for k in keys if lab(A, k) != lab(B, k)]
print(f"n={len(keys)}  agreement={len(agree)}/{len(keys)} ({len(agree)/len(keys)*100:.0f}%)  kappa={kappa:.2f}")
print(f"disagreements ({len(disagree)}): {disagree}")
# GT = agreement set (primary); disagreements need adjudication
gt = {k: (lab(A, k) == "GOOD") for k in agree}
for grp in ["Bank", "CreditReportLender", "ALL"]:
    ks = [k for k in agree if (grp == "ALL" or k.startswith(grp))]
    t = np.array([trust[k] for k in ks]); good = np.array([gt[k] for k in ks])
    nbad = int((~good).sum())
    if nbad < 2 or len(set(good.tolist())) < 2:
        print(f"{grp:20} n={len(ks)} GOOD={int(good.sum())} BAD={nbad} -> too few for AUROC"); continue
    auc = roc_auc_score(good, t); rej = t < 85
    print(f"{grp:20} n={len(ks)} GOOD={int(good.sum())} BAD={nbad} | AUROC={auc:.3f} | bad-catch@85={(~good&rej).sum()}/{nbad}={(~good&rej).sum()/nbad:.2f} | false-reject={(good&rej).sum()}/{int(good.sum())}={(good&rej).sum()/max(1,int(good.sum())):.2f}")
json.dump({"keys":keys,"disagree":disagree,"kappa":round(float(kappa),3),
           "gt_good":{k:gt[k] for k in agree}}, open(f"{SC}/gt_reconcile.json","w"), indent=1)
