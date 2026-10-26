#!/usr/bin/env python3
"""Compute the COMPETITOR'S metrics (AUROC + coverage at fixed error) on OUR decisions,
present-field, so the Jin et al. (2609.20110) head-to-head is like-for-like."""
import json, re, sys
from pathlib import Path
NTP="/Users/rajeshgupta/Git_Clones/NTP/NTP"; sys.path.insert(0,NTP)
import compute_roi  # noqa
EBV=next(p for p in Path(__file__).resolve().parents if p.name=="ebv_paper")
EXP=EBV/"experiments"; V2=EXP/"structured_ntp/fatura"; RES=EXP/"results"/"fatura_results"
AL=re.compile(r"[^a-z0-9]+")
RAW=json.loads((RES/"ground_truth_fatura.json").read_text())
CLEAN=json.loads((V2/"gt_clean"/"ground_truth_fatura_clean.json").read_text())
R=json.loads((RES/"extraction_results_fatura.json").read_text()); EXk=next(iter(next(iter(R.values())).keys()))
def pof(d,f): return (R.get(d,{}).get(EXk,{}).get("extracted") or {}).get(f)
def contain(p,g):
    p,g=AL.sub("",(p or "").lower()),AL.sub("",(g or "").lower())
    return (p==g if len(p)<2 else (p in g or g in p)) if p and g else False
def nex(g,p,f):
    try: return bool(compute_roi.values_match_field_aware(g,p,f))
    except TypeError: return bool(compute_roi.values_match_field_aware(g,p))
def corr(d,f,mode):
    p=pof(d,f)
    if p is None: return None
    if mode=="exact":
        cg=CLEAN.get(d,{}).get(f); return nex(cg,str(p),f) if cg is not None else None
    rg=RAW.get(d,{}).get(f); return contain(str(p),rg) if rg is not None else None
def auroc(pairs):  # pairs=(score,label_correct)
    pos=[s for s,c in pairs if c]; neg=[s for s,c in pairs if not c]
    if not pos or not neg: return None
    allp=sorted(pairs,key=lambda x:x[0])
    ranks={}; i=0
    # average ranks for ties
    vals=[s for s,_ in allp]
    import statistics  # noqa
    r=[0]*len(allp); j=0
    while j<len(allp):
        k=j
        while k+1<len(allp) and allp[k+1][0]==allp[j][0]: k+=1
        avg=(j+k)/2+1
        for t in range(j,k+1): r[t]=avg
        j=k+1
    sr=sum(r[idx] for idx,(s,c) in enumerate(allp) if c)
    npos,nneg=len(pos),len(neg)
    return (sr-npos*(npos+1)/2)/(npos*nneg)
def cov_at_risk(rows,targets=(0.05,0.10,0.20)):
    # rows=(wv_or_None, correct); accepted = wv>=t (unlocated never accepted)
    n=len(rows); scored=[(s,c) for s,c in rows if s is not None]
    out={}
    for tgt in targets:
        best=0.0
        for i in range(0,101):
            t=i/100; acc=[c for s,c in scored if s>=t]
            if not acc: continue
            risk=sum(1 for c in acc if not c)/len(acc)
            if risk<=tgt: best=max(best,len(acc)/n)
        out[tgt]=best
    return out
def run(name,path,mode):
    rows=[]
    for l in open(V2/path):
        r=json.loads(l); c=corr(r["doc"],r["field"],mode)
        if c is None: continue
        rows.append((r.get("wv_score"),c))
    a=auroc([(s,c) for s,c in rows if s is not None])
    cov=cov_at_risk(rows)
    print(f"{name:28} {mode:11} n={len(rows):6} AUROC={a:.4f}  cov@5%={cov[0.05]*100:4.1f}  cov@10%={cov[0.10]*100:4.1f}  cov@20%={cov[0.20]*100:4.1f}")
print("OUR spatial ROI verifier (present-field), competitor metrics:")
run("v2 pred-ROI calib","task3a_predroi_exact/decisions.jsonl","exact")
run("v2 pred-ROI calib","task1_predroi_containment/decisions.jsonl","containment")
run("v3 GT-ROI calib (prod)","task3b_gt_endtoend_exact/decisions.jsonl","exact")
run("v3 GT-ROI calib (prod)","matrix/v3cont_gt_calib_contain/decisions.jsonl","containment")
