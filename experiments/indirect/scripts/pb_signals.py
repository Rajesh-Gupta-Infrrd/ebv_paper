import json, glob, os, sys, random
sys.path.insert(0, "/Users/rajeshgupta/Projects/DocAI")
from scripts.extract.table_extractor.scoring import score_table_trust
IMG = "/Users/rajeshgupta/Projects/DocAI/eval/table_extraction/parsebench/table_trust_eval/images"
OUT = "/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/indirect/analysis/pb_signals.json"

def tblocks(o):
    out = []
    def walk(x):
        if isinstance(x, dict):
            mc = x.get("mineru_content")
            if isinstance(mc, str) and "<table" in mc.lower() and "bbox" in x: out.append(x)
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(o); return out

def jsonify(x):
    if isinstance(x, dict): return {k: jsonify(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [jsonify(v) for v in x]
    if isinstance(x, (bool, int, float, str)) or x is None: return x
    if hasattr(x, "item"):
        try: return x.item()
        except Exception: pass
    if hasattr(x, "__dict__"): return jsonify(vars(x))
    return str(x)

docs = glob.glob("/Users/rajeshgupta/Projects/DocAI/eval/table_extraction/parsebench/outputs/mineru_v3/*.json")
single = []
for fp in docs:
    o = json.load(open(fp)); t = tblocks(o)
    base = os.path.splitext(os.path.basename(fp))[0]
    if len(t) == 1 and os.path.exists(f"{IMG}/{base}.png"):
        single.append((base, o, t[0]))
random.seed(42); random.shuffle(single)   # SAME seed-42 sample as pb_manifest
man = []
for i, (base, o, blk) in enumerate(single[:60]):
    html = blk["mineru_content"]; nb = blk["bbox"]["normalized"]
    res = score_table_trust(table_html=html, image_path=f"{IMG}/{base}.png",
                            table_bbox_norm=(nb["x1"], nb["y1"], nb["x2"], nb["y2"]),
                            run_doctr_if_needed=True)
    sig = getattr(res, "signals", None)
    man.append({"i": i, "base": base,
                "trust": jsonify(getattr(res, "base_trust_score", None)),
                "codes": jsonify(getattr(res, "reason_codes", None)),
                "critical": jsonify(getattr(res, "critical", None)),
                "failure_family_hint": jsonify(getattr(res, "failure_family_hint", None)),
                "signals": jsonify(sig)})
    print(f"{i} trust={man[-1]['trust']} codes={man[-1]['codes']}", file=sys.stderr)
json.dump(man, open(OUT, "w"), indent=1, default=str)
print(f"wrote {len(man)} -> {OUT}", file=sys.stderr)
