"""C3: compare oracle test-sweep coverage (current) vs a real calibration-split threshold.
For each domain: split DOCS 50/50 into calib/test (seeded). Pick the smallest accept
threshold on calib with calib error <=5%. Apply that fixed threshold to the test docs;
report test coverage and realised test error. Average over 20 seeds."""
import json, glob, numpy as np
from collections import defaultdict

FILES = {
 "FCC":"experiments/unstructured_ntp/realkie_fcc/decisions/fcc_decisions_clean.jsonl",
 "S1":"experiments/unstructured_ntp/realkie_s1/decisions/realkie_s1_clean.jsonl",
 "Charities":"experiments/unstructured_ntp/realkie_charities/decisions/realkie_charities_clean.jsonl",
}
BASE="/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/"

def load(f):
    rows=[]
    for l in open(BASE+f):
        d=json.loads(l)
        s=d.get("proba");
        if s is None: s=d.get("final_score")
        if s is None: continue
        # scalar fields only (match paper): field_type non-lineitem
        rows.append((d["doc"], float(s), 1 if d["correct"] else 0))
    return rows

def oracle_cov(rows, tgt=0.05):
    s=np.array([r[1] for r in rows]); y=np.array([r[2] for r in rows]); n=len(y); best=0
    for t in np.unique(s)[::-1]:
        acc=s>=t
        if acc.sum() and (1-y[acc].mean())<=tgt: best=max(best,acc.mean())
    return best

def calib_cov(rows, tgt=0.05, seeds=20):
    docs=sorted(set(r[0] for r in rows)); covs=[]; risks=[]
    by=defaultdict(list)
    for r in rows: by[r[0]].append(r)
    for sd in range(seeds):
        rng=np.random.RandomState(sd); perm=list(docs); rng.shuffle(perm)
        half=len(perm)//2; cal=set(perm[:half]); tst=set(perm[half:])
        cr=[r for d in cal for r in by[d]]; tr=[r for d in tst for r in by[d]]
        cs=np.array([r[1] for r in cr]); cy=np.array([r[2] for r in cr])
        # smallest threshold with calib error <= tgt (maximise calib coverage)
        thr=None
        for t in np.unique(cs)[::-1]:
            acc=cs>=t
            if acc.sum() and (1-cy[acc].mean())<=tgt: thr=t
            elif acc.sum() and (1-cy[acc].mean())>tgt: break
        if thr is None: covs.append(0.0); risks.append(0.0); continue
        ts=np.array([r[1] for r in tr]); ty=np.array([r[2] for r in tr])
        acc=ts>=thr
        covs.append(acc.mean()); risks.append((1-ty[acc].mean()) if acc.sum() else 0.0)
    return np.mean(covs), np.mean(risks)

print(f"{'domain':10} {'n':>6} {'baserr':>7} {'ORACLE cov@5':>13} {'CALIB cov':>10} {'CALIB realised risk':>20}")
for dom,f in FILES.items():
    rows=load(f); n=len(rows); be=1-np.mean([r[2] for r in rows])
    oc=oracle_cov(rows); cc,cr=calib_cov(rows)
    print(f"{dom:10} {n:6} {be*100:6.1f}% {oc*100:12.0f}% {cc*100:9.0f}% {cr*100:19.1f}%")
