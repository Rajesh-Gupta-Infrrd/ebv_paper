import sys, json, glob, os
sys.path.insert(0, "/Users/rajeshgupta/Projects/DocAI")
sys.path.insert(0, "/Users/rajeshgupta/Projects/DocAI/scripts/extract/table_extractor")
from scripts.extract.table_extractor.scoring import score_table_trust
import pymupdf as fitz

RK = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/datasets/rocket/CD_tables"
PRED = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/results/rocket_preds/CD_tables/mineru"
OUT = "/private/tmp/claude-505/-Users-rajeshgupta-Projects-DocAI/dcbf7cdb-afa7-4247-b410-36141681f0c1/scratchpad/rocket_cd_tables"
os.makedirs(OUT, exist_ok=True)
N = 45

# pick the largest substantive table per doc, across docs, until N
cands = []
for mf in sorted(glob.glob(f"{PRED}/*.json")):
    d = json.load(open(mf)); rid = d["requestId"]
    blocks = []
    for pg in d.get("pages", []):
        for b in (pg.get("content_list") or []):
            if b.get("type") == "table" and b.get("content") and b.get("bbox") and len(b["content"]) > 300:
                blocks.append((pg["page_idx"], b["bbox"], b["content"]))
    if blocks:
        blocks.sort(key=lambda x: -len(x[2])); cands.append((rid, blocks[0]))
cands = cands[:N]
print(f"scoring {len(cands)} CD tables", flush=True)

man = []
for i, (rid, (pidx, bbox, html)) in enumerate(cands):
    pdfs = glob.glob(f"{RK}/{rid}*.pdf")
    if not pdfs: continue
    doc = fitz.open(pdfs[0]); pidx = min(pidx, len(doc)-1); page = doc[pidx]
    W, H = page.rect.width, page.rect.height
    pageimg = f"{OUT}/_page_{i}.png"; page.get_pixmap(dpi=150).save(pageimg)
    x0,y0,x1,y1 = bbox
    clip = fitz.Rect(x0*W, y0*H, x1*W, y1*H)
    crop = f"{OUT}/crop_{i}.png"; page.get_pixmap(dpi=170, clip=clip).save(crop); doc.close()
    try:
        res = score_table_trust(table_html=html, image_path=pageimg, run_doctr_if_needed=True, table_bbox_norm=(x0,y0,x1,y1))
        trust = round(float(res.base_trust_score), 1)
        rc = list(res.reason_codes); fam = res.failure_family_hint
    except Exception as e:
        trust = None; rc = [f"ERR:{type(e).__name__}"]; fam = None
        print(f"  [{i}] {rid[:10]} FAIL {str(e)[:80]}", flush=True)
    os.remove(pageimg)
    man.append({"i": i, "rid": rid, "trust": trust, "reason_codes": rc, "family": fam,
                "crop": crop, "html": html})
    if (i+1) % 10 == 0: print(f"  {i+1}/{len(cands)} done", flush=True)
json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)
trusts = [m["trust"] for m in man if m["trust"] is not None]
print(f"\nscored {len(trusts)} | trust: min={min(trusts):.0f} median={sorted(trusts)[len(trusts)//2]:.0f} max={max(trusts):.0f}")
print(f">=85 (accept): {sum(1 for t in trusts if t>=85)} | <85 (reject): {sum(1 for t in trusts if t<85)}")
print(f"manifest -> {OUT}/manifest.json")
print("DONE")
