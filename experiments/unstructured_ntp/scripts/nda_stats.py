import json, numpy as np
from collections import defaultdict
from sklearn.metrics import roc_auc_score

F="/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/unstructured_ntp/realkie_nda/decisions/realkie_nda_clean.jsonl"
rows=[json.loads(l) for l in open(F)]
print(f"n = {len(rows)} field decisions")
y=np.array([1 if r["correct"] else 0 for r in rows])
p=np.array([float(r["proba"]) if r["proba"] is not None else float(r["final_score"]) for r in rows])
docs=[r["doc"] for r in rows]
base_err=1-y.mean()
print(f"base error = {base_err*100:.1f}%   (correct={y.sum()}, errors={(1-y).sum()})")

def auroc(yv,sv):
    yv=np.asarray(yv); sv=np.asarray(sv)
    if len(set(yv))<2: return None
    return roc_auc_score(yv,sv)

print(f"\nAUROC(proba)            = {auroc(y,p):.4f}")

# doc-clustered bootstrap CI
by=defaultdict(list)
for i,d in enumerate(docs): by[d].append(i)
ud=list(by); rng=np.random.RandomState(0); vals=[]
for _ in range(2000):
    samp=[i for d in (rng.choice(ud) for _ in ud) for i in by[d]]
    ys=y[samp]; ps=p[samp]
    if len(set(ys))<2: continue
    vals.append(roc_auc_score(ys,ps))
vals.sort()
lo,hi=vals[int(.025*len(vals))],vals[int(.975*len(vals))]
print(f"  doc-clustered 95% CI   = [{lo:.3f}, {hi:.3f}]  (n_boot={len(vals)})")

# prior AUROC (gt_empty_rate) and presence (value_in_text)
gep=[r.get("gt_empty_rate") for r in rows]
n_gep=sum(1 for g in gep if g is not None)
print(f"\nprior (gt_empty_rate): non-null {n_gep}/{len(rows)}", end="  ")
if n_gep and len(set(g for g in gep if g is not None))>1:
    mask=[g is not None for g in gep]
    pa=auroc(y[mask],[g for g in gep if g is not None])
    print(f"-> AUROC = {pa}")
else:
    print("-> n/a (no usable variance)")

vit=[r["signals"].get("value_in_text") for r in rows]
vit_num=[1.0 if v is True else (0.0 if v is False else None) for v in vit]
mask=[v is not None for v in vit_num]
if sum(mask) and len(set(v for v in vit_num if v is not None))>1:
    pres=auroc(y[mask],[v for v in vit_num if v is not None])
    print(f"presence (value_in_text): non-null {sum(mask)}/{len(rows)} -> AUROC = {pres:.4f}")
else:
    print(f"presence (value_in_text): non-null {sum(mask)} -> n/a")

# coverage: oracle + calibrated (replicate calibration_coverage.py)
def oracle_cov(s,yv,tgt=0.05):
    best=0
    for t in np.unique(s)[::-1]:
        acc=s>=t
        if acc.sum() and (1-yv[acc].mean())<=tgt: best=max(best,acc.mean())
    return best
def calib_cov(rws,tgt=0.05,seeds=20):
    by=defaultdict(list)
    for r in rws: by[r[0]].append(r)
    dd=sorted(by); covs=[]; risks=[]
    for sd in range(seeds):
        rng=np.random.RandomState(sd); perm=list(dd); rng.shuffle(perm)
        h=len(perm)//2; cal=set(perm[:h]); tst=set(perm[h:])
        cr=[r for d in cal for r in by[d]]; tr=[r for d in tst for r in by[d]]
        cs=np.array([r[1] for r in cr]); cy=np.array([r[2] for r in cr])
        thr=None
        for t in np.unique(cs)[::-1]:
            acc=cs>=t
            if acc.sum() and (1-cy[acc].mean())<=tgt: thr=t
            elif acc.sum() and (1-cy[acc].mean())>tgt: break
        if thr is None: covs.append(0.0); risks.append(0.0); continue
        ts=np.array([r[1] for r in tr]); ty=np.array([r[2] for r in tr])
        acc=ts>=thr
        covs.append(acc.mean()); risks.append((1-ty[acc].mean()) if acc.sum() else 0.0)
    return np.mean(covs),np.mean(risks)
rws=[(docs[i],p[i],y[i]) for i in range(len(rows))]
oc=oracle_cov(p,y)
cc,crisk=calib_cov(rws)
print(f"\noracle cov@5%            = {oc*100:.0f}%")
print(f"CALIBRATED cov@5%        = {cc*100:.0f}%   realised test risk = {crisk*100:.1f}%")

# 12i: binary vs 3-tier catch + safeguard firing
err=(y==0)
for mode in ["accept_bin","accept_3t"]:
    acc=np.array([bool(r[mode]) for r in rows])
    caught=int(((~acc)&err).sum()); total_err=int(err.sum())
    print(f"\n[{mode}] catch rate = {caught}/{total_err} = {caught/total_err*100:.0f}%   coverage(accept all)={acc.mean()*100:.0f}%")
n_prior=sum(1 for r in rows if r.get("empty_prior_applied") not in (None,))
n_gated=sum(1 for r in rows if r.get("gated") not in (None,))
print(f"\nsafeguards fired on NDA: empty_prior_applied={n_prior}  gated(hard gate)={n_gated}")
