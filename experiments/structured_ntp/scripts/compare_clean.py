#!/usr/bin/env python3
"""
Validate: does cleaning absent fields BEFORE the pipeline change present-field results?
Compare cleaned-input v2 runs vs original full-input v2 runs (filtered to present fields):
  - per-(doc,field) accept/route agreement
  - catch / false-alarm computed both ways
If accept decisions match -> present-field table is validated (per-field independence).
"""
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
def load_accept(path, present_filter):
    out={}
    for l in open(V2/path):
        r=json.loads(l)
        if r.get("accept") is None: continue
        if present_filter and RAW.get(r["doc"],{}).get(r["field"]) is None: continue
        out[(r["doc"],r["field"])]=bool(r["accept"])
    return out
def metrics(accept_map, mode):
    TN=FP=TP=FN=0
    for (d,f),a in accept_map.items():
        c=corr(d,f,mode)
        if c is None: continue
        if c and a:TN+=1
        elif c and not a:FP+=1
        elif not c and not a:TP+=1
        else:FN+=1
    w=TP+FN; co=TN+FP
    return dict(n=TN+FP+TP+FN, catch=(TP/w if w else None), fa=(FP/co if co else None), acc=((TP+TN)/(TN+FP+TP+FN)))
def compare(mode, clean_path, orig_path):
    cl=load_accept(clean_path, present_filter=False)   # clean run already present-only
    og=load_accept(orig_path, present_filter=True)     # filter original to present
    keys=set(cl)&set(og)
    disagree=sum(1 for k in keys if cl[k]!=og[k])
    print(f"=== {mode} ===")
    print(f"  keys: clean={len(cl)} orig(present)={len(og)} common={len(keys)}")
    print(f"  accept/route DISAGREEMENTS: {disagree} ({disagree/len(keys)*100:.2f}%)")
    mc=metrics(cl,mode); mo=metrics(og,mode)
    print(f"  clean-run : n={mc['n']} catch={mc['catch']:.4f} fa={mc['fa']:.4f} acc={mc['acc']:.4f}")
    print(f"  orig-filt : n={mo['n']} catch={mo['catch']:.4f} fa={mo['fa']:.4f} acc={mo['acc']:.4f}")
compare("exact","matrix/v2clean_exact/decisions.jsonl","task3a_predroi_exact/decisions.jsonl")
compare("containment","matrix/v2clean_contain/decisions.jsonl","task1_predroi_containment/decisions.jsonl")
