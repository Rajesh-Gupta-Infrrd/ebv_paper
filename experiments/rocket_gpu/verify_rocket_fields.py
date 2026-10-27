import json, re, glob, os
import numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score

ROOT = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/datasets/rocket"
PRED = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/results/rocket_preds"
ROI_TYPES = {"URLA", "CD_tables"}          # structured leg (spatial grounding)
SIGNAL_TYPES = {"AUS_DU", "Bank", "CreditReportLender"}
TYPES = ["URLA", "CD_tables", "AUS_DU", "Bank", "CreditReportLender"]
AL = re.compile(r"[^a-z0-9]+")
def norm(x): return AL.sub("", str(x).lower()) if x not in (None, "") else ""
def contain(p, g):
    p, g = norm(p), norm(g)
    if not p and not g: return True
    if not p or not g: return False
    return p == g if len(p) < 3 else (p in g or g in p)

def ocr_text(rid, typ):
    f = f"{ROOT}/{typ}/ocr/{rid}.json"
    if not os.path.exists(f): return "", []
    try:
        d = json.load(open(f))
    except Exception:
        return "", []
    txt = []; toks = []
    for pg in d.get("pages", []):
        rt = pg.get("rawText")
        if isinstance(rt, str): txt.append(rt)
        for t in (pg.get("tokens") or []):
            if isinstance(t, dict) and t.get("text"):
                toks.append(t)
    return norm(" ".join(txt)), toks

def gt_bbox(rid, typ):
    f = f"{ROOT}/{typ}/fields/{rid}.json"
    if not os.path.exists(f): return {}
    out = {}
    for fld in json.load(open(f)).get("fields", []):
        if fld.get("bbox"): out[fld["fieldName"]] = fld["bbox"]
    return out

def roi_grounded(pred, bbox, toks):
    """1 if predicted value's tokens appear in OCR within/near the GT bbox region."""
    if not bbox or not pred: return 0.0
    pn = norm(pred)
    cand = [t for t in toks if norm(t.get("text")) and norm(t.get("text")) in pn]
    if not cand: return 0.0
    bx0,by0,bx1,by1 = bbox.get("startX"),bbox.get("startY"),bbox.get("endX"),bbox.get("endY")
    pg = bbox.get("pageNumber")
    for t in cand:
        if pg is not None and t.get("pageNumber") not in (pg, None): continue
        tx0,ty0,tx1,ty1 = t.get("startX",0),t.get("startY",0),t.get("endX",0),t.get("endY",0)
        # overlap of token box with gt box (with slack)
        if None in (bx0,by0,bx1,by1): return 1.0
        if tx1>=bx0-50 and tx0<=bx1+50 and ty1>=by0-50 and ty0<=by1+50:
            return 1.0
    return 0.0

summary = []
for typ in TYPES:
    chosen = json.load(open(f"{ROOT}/{typ}/field_list.json"))["fields"]
    rows = []
    # field empty-rate prior from GT
    gt_all = {}
    for gf in glob.glob(f"{ROOT}/{typ}/gt/*.json"):
        g = json.load(open(gf)); gt_all[g["requestId"]] = g["gt"]
    emptyrate = {}
    for fn in chosen:
        vals = [gt_all[r].get(fn) for r in gt_all if fn in gt_all[r]]
        emptyrate[fn] = np.mean([1.0 if v in (None,"") else 0.0 for v in vals]) if vals else 0.0
    for pf in glob.glob(f"{PRED}/{typ}/nuextract/*.json"):
        p = json.load(open(pf)); rid = p["requestId"]; ex = p.get("extracted") or {}
        if rid not in gt_all: continue
        gt = gt_all[rid]; octxt, toks = ocr_text(rid, typ); bb = gt_bbox(rid, typ) if typ in ROI_TYPES else {}
        for fn in chosen:
            if fn not in gt: continue
            pred = ex.get(fn); g = gt.get(fn)
            correct = contain(pred, g)
            s_empty = 1.0 if (pred is None or str(pred).strip()=="") else 0.0
            s_in_ocr = 1.0 if (not s_empty and norm(pred) and norm(pred) in octxt) else 0.0
            s_roi = roi_grounded(pred, bb.get(fn), toks) if typ in ROI_TYPES else np.nan
            rows.append({"doc": rid, "field": fn, "correct": int(correct),
                         "s_empty": s_empty, "s_in_ocr": s_in_ocr,
                         "s_emptyrate": emptyrate.get(fn,0.0), "s_roi": s_roi,
                         "s_len": len(str(pred)) if pred else 0})
    df = pd.DataFrame(rows)
    feats = ["s_empty","s_in_ocr","s_emptyrate","s_len"] + (["s_roi"] if typ in ROI_TYPES else [])
    X = df[feats].fillna(-1).values; y = df["correct"].values; grp = df["doc"].values
    nerr = int((y==0).sum())
    if len(np.unique(y)) < 2 or nerr < 3:
        print(f"{typ:20} n={len(df)} errors={nerr} -> too few errors to score"); continue
    oof = np.zeros(len(df))
    for tr,te in GroupKFold(min(5, df['doc'].nunique())).split(X,y,grp):
        m = GradientBoostingClassifier(random_state=0).fit(X[tr],y[tr]); oof[te]=m.predict_proba(X[te])[:,1]
    auc = roc_auc_score(y, oof)
    # coverage @ <=5% risk (accept highest-proba)
    order = np.argsort(-oof); cov = 0.0
    for t in np.unique(oof)[::-1]:
        acc = oof>=t
        if acc.sum() and (1-y[acc].mean())<=0.05: cov = acc.mean()
        elif acc.sum() and (1-y[acc].mean())>0.05: break
    leg = "ROI/structured" if typ in ROI_TYPES else "Signal/unstructured"
    print(f"{typ:20} [{leg:18}] n={len(df):5} errors={nerr:4} err_rate={(y==0).mean()*100:4.1f}%  AUROC={auc:.3f}  coverage@<=5%={cov*100:.0f}%")
    summary.append({"type":typ,"leg":leg,"n":len(df),"errors":nerr,"auroc":round(auc,3),"coverage@5":round(cov,3)})
json.dump(summary, open("/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/results/rocket_preds/rocket_fields_summary.json","w"), indent=1)
print("\nsaved -> results/rocket_preds/rocket_fields_summary.json")
