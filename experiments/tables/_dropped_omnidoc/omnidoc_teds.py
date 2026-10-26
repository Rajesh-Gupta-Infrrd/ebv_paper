import json, os, sys, glob
import importlib.util as _u
_spec=_u.spec_from_file_location("tm","eval/parse/omnidoc-bench/OmniDocBench-code/src/metrics/table_metric.py")
_tm=_u.module_from_spec(_spec); _spec.loader.exec_module(_tm); TEDS=_tm.TEDS
teds = TEDS(structure_only=False)
def wrap(h): return f"<html><body>{h}</body></html>"

# 1. GT: basename(no ext) -> list of table htmls
GT={}
for p in json.load(open("eval/parse/omnidoc-bench/OmniDocBench/OmniDocBench.json")):
    img=p["page_info"]["image_path"]; base=os.path.splitext(img)[0]
    tbls=[l["html"] for l in p.get("layout_dets",[]) if l.get("category_type")=="table" and l.get("html")]
    if tbls: GT[base]=tbls

# 2. predicted table blocks per case
CASES="eval/parse/omnidoc-bench/outputs/auto_table_refined/auto/cases"
def orig_html(b):
    for k in b:
        if k.endswith("_content_original"): return b[k]
    for k in b:
        if k.endswith("_content") and k!="glmocr_native_label": return b[k]
    return None
recs=[]; n_blocks=0; n_casestbl=0; multi=0; no_gt=0
for case in os.listdir(CASES):
    ds=os.path.join(CASES,case,"document_surface.json")
    if not os.path.exists(ds): continue
    try: d=json.load(open(ds))
    except: continue
    blocks=[]
    for pg in d.get("pages",[]):
        for b in pg.get("blocks",[]):
            if isinstance(b,dict) and "table_refinement" in b:
                blocks.append(b)
    if not blocks: continue
    n_casestbl+=1; n_blocks+=len(blocks)
    gt=GT.get(case)
    if not gt: no_gt+=1; continue
    # clean 1:1 only: exactly one predicted table block AND one GT table
    if len(blocks)!=1 or len(gt)!=1:
        multi+=1; continue
    b=blocks[0]; ph=orig_html(b); tr=b.get("table_refinement",{})
    tb=tr.get("trust_score_before")
    if ph is None or tb is None: continue
    t=teds.evaluate(wrap(ph), wrap(gt[0]))
    import re as _re
    eq=len(_re.findall(r"\$|\\\\|<math|\\\(", gt[0]))
    recs.append({"case":case,"trust_before":tb,"teds":round(t,4),"status":tr.get("status"),"eq":eq,"gtlen":len(gt[0])})
json.dump(recs, open("/private/tmp/claude-505/-Users-rajeshgupta-Projects-DocAI/dcbf7cdb-afa7-4247-b410-36141681f0c1/scratchpad/omnidoc_teds.json","w"), indent=1)
print(f"cases with table blocks: {n_casestbl} | total blocks: {n_blocks} | multi/skip: {multi} | no GT match: {no_gt}")
print(f"clean 1:1 tables scored (TEDS): {len(recs)}")
import statistics
td=[r["teds"] for r in recs]; tr=[r["trust_before"] for r in recs]
if td:
    print(f"TEDS: min {min(td):.3f} median {statistics.median(td):.3f} max {max(td):.3f} | good@0.9 {sum(1 for x in td if x>=0.9)}/{len(td)} ({sum(1 for x in td if x>=0.9)/len(td)*100:.0f}%)")
    print(f"trust: min {min(tr):.1f} median {statistics.median(tr):.1f} max {max(tr):.1f}")
