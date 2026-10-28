"""C7 fix: ROCKET ROI with region LEARNED from training folds (no test-doc gold box).
Compares the leaky version (test-doc gt_bbox) vs the proper version (train-learned ROI)."""
import json, re, glob, os
import numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score

ROOT = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/datasets/rocket"
PRED = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/results/rocket_preds"
ROI_TYPES = ["URLA", "CD_tables"]
AL = re.compile(r"[^a-z0-9]+")
def norm(x): return AL.sub("", str(x).lower()) if x not in (None, "") else ""
def contain(p, g):
    p, g = norm(p), norm(g)
    if not p and not g: return True
    if not p or not g: return False
    return p == g if len(p) < 3 else (p in g or g in p)
def ocr_toks(rid, typ):
    f = f"{ROOT}/{typ}/ocr/{rid}.json"
    if not os.path.exists(f): return []
    try: d = json.load(open(f))
    except Exception: return []
    return [t for pg in d.get("pages", []) for t in (pg.get("tokens") or []) if isinstance(t, dict) and t.get("text")]
def gt_bbox(rid, typ):
    f = f"{ROOT}/{typ}/fields/{rid}.json"
    if not os.path.exists(f): return {}
    return {fl["fieldName"]: fl["bbox"] for fl in json.load(open(f)).get("fields", []) if fl.get("bbox")}
def box_tuple(b):
    return (b.get("startX"), b.get("startY"), b.get("endX"), b.get("endY"), b.get("pageNumber"))
def pred_token_boxes(pred, toks):
    pn = norm(pred)
    return [t for t in toks if norm(t.get("text")) and norm(t.get("text")) in pn]
def near(tb, roi, slack=50):
    bx0,by0,bx1,by1,pg = roi
    if None in (bx0,by0,bx1,by1): return True
    for t in tb:
        if pg is not None and t.get("pageNumber") not in (pg, None): continue
        tx0,ty0,tx1,ty1 = t.get("startX",0),t.get("startY",0),t.get("endX",0),t.get("endY",0)
        if tx1>=bx0-slack and tx0<=bx1+slack and ty1>=by0-slack and ty0<=by1+slack: return True
    return False

print(f"{'type':12} {'leg':8} {'n':>6} {'LEAKY AUROC':>12} {'PROPER AUROC':>13} {'LEAKY cov':>10} {'PROPER cov':>11}")
for typ in ROI_TYPES:
    chosen = json.load(open(f"{ROOT}/{typ}/field_list.json"))["fields"]
    gt_all = {}
    for gf in glob.glob(f"{ROOT}/{typ}/gt/*.json"):
        g = json.load(open(gf)); gt_all[g["requestId"]] = g["gt"]
    emptyrate = {}
    for fn in chosen:
        vals = [gt_all[r].get(fn) for r in gt_all if fn in gt_all[r]]
        emptyrate[fn] = np.mean([1.0 if v in (None,"") else 0.0 for v in vals]) if vals else 0.0
    rows = []
    for pf in glob.glob(f"{PRED}/{typ}/nuextract/*.json"):
        p = json.load(open(pf)); rid = p["requestId"]; ex = p.get("extracted") or {}
        if rid not in gt_all: continue
        gt = gt_all[rid]; toks = ocr_toks(rid, typ); bb = gt_bbox(rid, typ)
        for fn in chosen:
            if fn not in gt: continue
            pred = ex.get(fn); g = gt.get(fn)
            tb = pred_token_boxes(pred, toks) if pred else []
            own_box = box_tuple(bb[fn]) if fn in bb else None
            s_empty = 1.0 if (pred is None or str(pred).strip()=="") else 0.0
            octxt = " ".join(norm(t.get("text")) for t in toks)
            s_in_ocr = 1.0 if (not s_empty and norm(pred) and norm(pred) in octxt) else 0.0
            # LEAKY s_roi: predicted token near THIS doc's own gold box
            s_roi_leak = 1.0 if (own_box and tb and near(tb, own_box)) else 0.0
            rows.append({"doc": rid, "field": fn, "correct": int(contain(pred, g)),
                         "s_empty": s_empty, "s_in_ocr": s_in_ocr, "s_emptyrate": emptyrate.get(fn,0.0),
                         "s_len": len(str(pred)) if pred else 0, "s_roi_leak": s_roi_leak,
                         "own_box": own_box, "tb": tb})
    df = pd.DataFrame(rows); grp = df["doc"].values; y = df["correct"].values

    def cov_at5(oof, y):
        best=0.0
        for t in np.unique(oof)[::-1]:
            acc = oof>=t
            if acc.sum() and (1-y[acc].mean())<=0.05: best=max(best, acc.mean())
        return best

    def run(use_proper):
        gk = GroupKFold(min(5, df['doc'].nunique()))
        oof = np.zeros(len(df))
        base = ["s_empty","s_in_ocr","s_emptyrate","s_len"]
        for tr, te in gk.split(df, y, grp):
            tr_docs = set(df.iloc[tr]["doc"])
            if use_proper:
                # learn per-field ROI (median box) from TRAIN docs only
                perf = {}
                for i in tr:
                    r = df.iloc[i]
                    if r["own_box"] and None not in r["own_box"][:4]:
                        perf.setdefault(r["field"], []).append(r["own_box"])
                roi = {}
                for fn, boxes in perf.items():
                    arr = np.array([b[:4] for b in boxes], float)
                    pgs = [b[4] for b in boxes]
                    pg = max(set(pgs), key=pgs.count) if pgs else None
                    roi[fn] = (float(np.median(arr[:,0])), float(np.median(arr[:,1])),
                               float(np.median(arr[:,2])), float(np.median(arr[:,3])), pg)
                sroi = np.array([1.0 if (r["field"] in roi and r["tb"] and near(r["tb"], roi[r["field"]], slack=80)) else 0.0
                                 for _, r in df.iterrows()])
            else:
                sroi = df["s_roi_leak"].values
            feats = np.column_stack([df[base].values, sroi]).astype(float)
            feats = np.nan_to_num(feats, nan=-1.0)
            m = GradientBoostingClassifier(random_state=0).fit(feats[tr], y[tr])
            oof[te] = m.predict_proba(feats[te])[:,1]
        return roc_auc_score(y, oof), cov_at5(oof, y)

    a_leak, c_leak = run(False)
    a_prop, c_prop = run(True)
    print(f"{typ:12} {'ROI':8} {len(df):6} {a_leak:12.3f} {a_prop:13.3f} {c_leak*100:9.0f}% {c_prop*100:10.0f}%")
