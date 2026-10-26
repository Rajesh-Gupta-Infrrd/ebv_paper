import json, os, random
from PIL import Image
ROOT="/Users/rajeshgupta/Projects/DocAI/eval/parse/omnidoc-bench/outputs/auto_table_refined/auto/cases"
SP="/private/tmp/claude-505/-Users-rajeshgupta-Projects-DocAI/dcbf7cdb-afa7-4247-b410-36141681f0c1/scratchpad"
recs=json.load(open(f"{SP}/omnidoc_teds.json"))
ROOTd="/Users/rajeshgupta/Projects/DocAI/eval/parse/omnidoc-bench/outputs/auto_table_refined/auto/cases"
recs=[r for r in recs if os.path.exists(f"{ROOTd}/{r['case']}/input.png")]
print("recs with input.png:",len(recs))
random.seed(42); sample=random.sample(recs,min(40,len(recs)))
cd=f"{SP}/omnidoc_crops"; os.makedirs(cd,exist_ok=True)
man=[]
for i,r in enumerate(sample):
    case=r["case"]; ds=f"{ROOT}/{case}/document_surface.json"
    d=json.load(open(ds)); blk=None
    for pg in d.get("pages",[]):
        for b in pg.get("blocks",[]):
            if isinstance(b,dict) and "table_refinement" in b: blk=b; break
        if blk: break
    nb=blk["bbox"]["normalized"]; html=None
    for k in blk:
        if k.endswith("_content_original"): html=blk[k]; break
    img=Image.open(f"{ROOT}/{case}/input.png").convert("RGB"); W,H=img.size
    box=(int(nb["x1"]*W),int(nb["y1"]*H),int(nb["x2"]*W),int(nb["y2"]*H))
    crop=img.crop(box); cp=f"{cd}/t{i:02d}.png"; crop.save(cp)
    man.append({"i":i,"case":case,"crop":cp,"html":html,"trust":r["trust_before"],"teds":r["teds"]})
json.dump(man,open(f"{SP}/omnidoc_vlm_manifest.json","w"),indent=1)
print(f"generated {len(man)} crops in {cd}")
print("trust range:", min(m['trust'] for m in man), max(m['trust'] for m in man))
print("teds>=0.9:", sum(1 for m in man if m['teds']>=0.9), "/", len(man))
