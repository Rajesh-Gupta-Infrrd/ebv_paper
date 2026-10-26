import json, glob, os, sys, random, argparse
sys.path.insert(0, "/Users/rajeshgupta/Projects/DocAI")
from scripts.extract.table_extractor.scoring import score_table_trust
IMG="eval/table_extraction/parsebench/table_trust_eval/images"
def tblocks(o):
    out=[]
    def walk(x):
        if isinstance(x,dict):
            mc=x.get("mineru_content")
            if isinstance(mc,str) and "<table" in mc.lower() and "bbox" in x: out.append(x)
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(o); return out
ap=argparse.ArgumentParser(); ap.add_argument("--n",type=int,default=3); ap.add_argument("--probe",action="store_true"); a=ap.parse_args()
docs=glob.glob("eval/table_extraction/parsebench/outputs/mineru_v3/*.json")
single=[]
for fp in docs:
    o=json.load(open(fp)); t=tblocks(o)
    base=os.path.splitext(os.path.basename(fp))[0]
    if len(t)==1 and os.path.exists(f"{IMG}/{base}.png"):
        single.append((fp,base,o,t[0]))
print(f"single-table w/ image: {len(single)}",file=sys.stderr)
random.seed(42); random.shuffle(single)
SP="/private/tmp/claude-505/-Users-rajeshgupta-Projects-DocAI/dcbf7cdb-afa7-4247-b410-36141681f0c1/scratchpad"
cd=f"{SP}/pb_crops"; os.makedirs(cd,exist_ok=True)
from PIL import Image
man=[]
for i,(fp,base,o,blk) in enumerate(single[:a.n]):
    html=blk["mineru_content"]; nb=blk["bbox"]["normalized"]
    img=f"{IMG}/{base}.png"
    res=score_table_trust(table_html=html, image_path=img,
          table_bbox_norm=(nb["x1"],nb["y1"],nb["x2"],nb["y2"]), run_doctr_if_needed=True)
    if a.probe and i==0:
        print("RESULT attrs:",[x for x in dir(res) if not x.startswith("_")],file=sys.stderr)
    trust=getattr(res,"base_trust_score",None) or getattr(res,"trust_score",None) or getattr(res,"score",None)
    rc=getattr(res,"reason_codes",None)
    # crop
    im=Image.open(img).convert("RGB"); W,H=im.size
    im.crop((int(nb["x1"]*W),int(nb["y1"]*H),int(nb["x2"]*W),int(nb["y2"]*H))).save(f"{cd}/p{i:02d}.png")
    man.append({"i":i,"base":base,"crop":f"{cd}/p{i:02d}.png","html":html,
                "trust":trust,"reason_codes":rc,"accept":(trust>=85 if trust is not None else None),
                "gt_md":o.get("expected_markdown")})
    print(f"{i} trust={trust} accept={trust is not None and trust>=85} base={base[:40]}",file=sys.stderr)
json.dump(man,open(f"{SP}/pb_manifest.json","w"),indent=1)
print(f"wrote {len(man)} -> {SP}/pb_manifest.json",file=sys.stderr)
