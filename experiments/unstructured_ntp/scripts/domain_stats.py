import json, numpy as np
from sklearn.metrics import roc_auc_score
BASE="/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/unstructured_ntp/"
F={"FCC":"realkie_fcc/decisions/fcc_decisions_clean.jsonl",
   "S1":"realkie_s1/decisions/realkie_s1_clean.jsonl",
   "Charities":"realkie_charities/decisions/realkie_charities_clean.jsonl",
   "NDA":"realkie_nda/decisions/realkie_nda_clean.jsonl"}
def auro(y,s):
    y=np.array(y); s=np.array(s)
    return roc_auc_score(y,s) if len(set(y))>1 and len(set(s))>1 else None
for dom,f in F.items():
    try: rows=[json.loads(l) for l in open(BASE+f)]
    except FileNotFoundError: print(f"{dom}: NO FILE {f}"); continue
    y=[1 if r["correct"] else 0 for r in rows]
    p=[float(r.get("proba") if r.get("proba") is not None else r.get("final_score")) for r in rows]
    gep=[r.get("gt_empty_rate") for r in rows]
    vit=[1.0 if r["signals"].get("value_in_text") is True else (0.0 if r["signals"].get("value_in_text") is False else None) for r in rows]
    err=np.array(y)==0; ne=int(err.sum())
    au=auro(y,p)
    # prior
    gm=[g is not None for g in gep]
    pa=auro([y[i] for i in range(len(y)) if gm[i]],[gep[i] for i in range(len(y)) if gm[i]]) if any(gm) and len(set(g for g in gep if g is not None))>1 else "n/a"
    vm=[v is not None for v in vit]
    pr=auro([y[i] for i in range(len(y)) if vm[i]],[vit[i] for i in range(len(y)) if vm[i]]) if any(vm) else "n/a"
    nprior=sum(1 for r in rows if r.get("empty_prior_applied") not in (None,))
    ngate=sum(1 for r in rows if r.get("gated") not in (None,))
    cbin=sum(1 for i,r in enumerate(rows) if err[i] and not bool(r.get("accept_bin")))
    c3t =sum(1 for i,r in enumerate(rows) if err[i] and not bool(r.get("accept_3t")))
    def fmt(x): return f"{x:.3f}" if isinstance(x,float) else str(x)
    print(f"{dom:10} n={len(rows):6} err={ne:5}  AUROC(proba)={fmt(au)}  prior={fmt(pa)}  presence={fmt(pr)}")
    print(f"           empty_prior_fires={nprior:5}  hard_gates_fire={ngate:4}  catch_binary={cbin}/{ne}  catch_3tier={c3t}/{ne}")
