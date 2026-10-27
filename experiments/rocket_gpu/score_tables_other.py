import sys, json, glob, os
sys.path.insert(0, "/Users/rajeshgupta/Projects/DocAI")
sys.path.insert(0, "/Users/rajeshgupta/Projects/DocAI/scripts/extract/table_extractor")
from scripts.extract.table_extractor.scoring import score_table_trust
import pymupdf as fitz
import numpy as np

RK = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/datasets/rocket"
PRED = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/results/rocket_preds"
OUT = "/private/tmp/claude-505/-Users-rajeshgupta-Projects-DocAI/dcbf7cdb-afa7-4247-b410-36141681f0c1/scratchpad/rocket_other_tables"
os.makedirs(OUT, exist_ok=True)
N = 40

for typ in ["Bank", "CreditReportLender"]:
    cands = []
    for mf in sorted(glob.glob(f"{PRED}/{typ}/mineru/*.json")):
        d = json.load(open(mf)); rid = d["requestId"]
        blocks = [(pg["page_idx"], b["bbox"], b["content"]) for pg in d.get("pages", [])
                  for b in (pg.get("content_list") or [])
                  if b.get("type") == "table" and b.get("content") and b.get("bbox") and len(b["content"]) > 400]
        if blocks:
            blocks.sort(key=lambda x: -len(x[2])); cands.append((rid, blocks[0]))
    cands = cands[:N]
    man = []
    for i, (rid, (pidx, bbox, html)) in enumerate(cands):
        pdfs = glob.glob(f"{RK}/{typ}/{rid}*.pdf")
        if not pdfs: continue
        doc = fitz.open(pdfs[0]); pidx = min(pidx, len(doc)-1); page = doc[pidx]
        W, H = page.rect.width, page.rect.height
        x0,y0,x1,y1 = bbox
        crop = f"{OUT}/{typ}_crop_{i}.png"
        page.get_pixmap(dpi=170, clip=fitz.Rect(x0*W,y0*H,x1*W,y1*H)).save(crop); doc.close()
        try:
            res = score_table_trust(table_html=html, image_path=crop, run_doctr_if_needed=True)
            trust = round(float(res.base_trust_score),1)
            tc = res.signals.get("text_conservation"); rec = tc.details.get("recall") if tc else None
        except Exception as e:
            trust=None; rec=None
        man.append({"i":i,"rid":rid,"trust":trust,"recall":round(rec,2) if rec else None,"crop":crop,"html":html})
    json.dump(man, open(f"{OUT}/{typ}_manifest.json","w"), indent=1)
    ts=[m["trust"] for m in man if m["trust"] is not None]
    print(f"{typ:20} scored={len(ts)}  median_recall={np.median([m['recall'] for m in man if m['recall']]):.2f}  "
          f"trust: median={np.median(ts):.0f} <85={sum(1 for t in ts if t<85)} (likely-BAD candidates)  spread={sorted(ts)[:5]}...{sorted(ts)[-3:]}", flush=True)
print("DONE")
