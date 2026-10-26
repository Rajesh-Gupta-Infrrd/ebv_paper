#!/usr/bin/env python3
"""Generate STRUCTURED_EXPERIMENT.md: both 8-row tables (full + present-only) computed
straight from the decision files, plus version/dir/finding documentation."""
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
def corr(d,f,mode,pop):
    p=pof(d,f)
    if p is None: return None
    if mode=="exact":
        cg=CLEAN.get(d,{}).get(f)
        if cg is not None: return nex(cg,str(p),f)
        return False if pop=="full" else None       # absent field + prediction = hallucination (full only)
    rg=RAW.get(d,{}).get(f)
    if rg is not None: return contain(str(p),rg)
    return False if pop=="full" else None
CELLS={("v1","exact"):"matrix/v1_pred_nocalib/decisions.jsonl",("v1","containment"):"matrix/v1_pred_nocalib/decisions.jsonl",
       ("v2","exact"):"task3a_predroi_exact/decisions.jsonl",("v2","containment"):"task1_predroi_containment/decisions.jsonl",
       ("v3","exact"):"task3b_gt_endtoend_exact/decisions.jsonl",("v3","containment"):"matrix/v3cont_gt_calib_contain/decisions.jsonl",
       ("v4","exact"):"matrix/v4_gt_nocalib/decisions.jsonl",("v4","containment"):"matrix/v4_gt_nocalib/decisions.jsonl"}
CFG={"v1":"pred-ROI, calib OFF","v2":"pred-ROI, calib ON","v3":"GT-ROI, calib ON (prod)","v4":"GT-ROI, calib OFF"}
def metrics(path,mode,pop):
    TN=FP=TP=FN=0; elig=[]
    for l in open(V2/path):
        r=json.loads(l)
        if r.get("accept") is None: continue
        c=corr(r["doc"],r["field"],mode,pop)
        if c is None: continue
        a=bool(r["accept"])
        if c and a:TN+=1
        elif c and not a:FP+=1
        elif not c and not a:TP+=1
        else:FN+=1
        if r.get("wv_score") is not None: elig.append((r["wv_score"],c))
    n=TN+FP+TP+FN; w=TP+FN; co=TN+FP
    pts=[]
    for i in range(101):
        t=i/100; acc=[c for s,c in elig if s>=t]; na=len(acc); aw=sum(1 for c in acc if not c)
        pts.append((na/n if n else 0, aw/na if na else 0))
    pts=sorted(set(pts)); aurc=sum((b[0]-a[0])*(a[1]+b[1])/2 for a,b in zip(pts,pts[1:]))
    f=lambda x:"—" if x is None else f"{x:.4f}"
    return (f"| {{v}} | {{cfg}} | {mode} | {n} | {w/n:.3f} | {f(TP/w if w else None)} | {f(FP/co if co else None)} | "
            f"{f(TP/(TP+FP) if (TP+FP) else None)} | {f((TP+TN)/n if n else None)} | {f(aurc)} |")
def table(pop):
    hdr=("| ver | config | correctness | n | err-rate | error-catch ↑ | false-alarm ↓ | route-prec ↑ | accuracy ↑ | AURC ↓ |\n"
         "|---|---|---|---|---|---|---|---|---|---|")
    rows=[hdr]
    for v in ["v1","v2","v3","v4"]:
        for m in ["exact","containment"]:
            rows.append(metrics(CELLS[(v,m)],m,pop).format(v=v,cfg=CFG[v]))
    return "\n".join(rows)
FULL=table("full"); PRES=table("present")
doc=f"""# Structured (ROI) NTP experiment — full documentation

Verifies document-extraction field values with NTP's spatial ROI verifier (no extra LLM/VLM call)
on **FATURA** (50 templates, 10,000 synthetic invoices). Extractor = NuExtract-3. All runs drive
NTP's real pipeline **offline** (no Mongo) via `/Users/rajeshgupta/Git_Clones/NTP/NTP/venv/bin/python`.

## Pipeline
`compute_roi_for_doc_type` (ROI geometry + per-field thresholds + context keywords) →
`calibrate_from_evaluation_dataframes` (grid-searched per-field weights + score threshold) →
`evaluate_doc_type` (spatial score + keyword-context boost + empty-field handling → accept/route).
Per-template 70/30 split (seed 42): 7,000 train / 3,000 test docs. Templates scored independently
(verified: cleaning absent fields before vs after the pipeline gives 0 decision differences).

## The two axes
- **ROI geometry source**: `pred` = learned from where the extractor's *correct* predictions land;
  `GT` = learned from the (cleaned) ground-truth values (production's way).
- **Weight calibration**: `ON` = grid-searched per-field weights+threshold; `OFF` = NTP defaults
  (overlap/center/iou = .50/.30/.20, score_threshold 0.70).
- **Correctness (a LABEL, not a pipeline toggle)**: `exact` = NTP field-aware matcher on cleaned GT;
  `containment` = normalized-alnum substring match (lenient; robust to FATURA's label-bundled GT).
- **Population**: `present` = fields that exist in the doc's GT (the honest spatial task);
  `full` = present + hallucinations on absent fields (trivially routed → inflates catch).

## Versions (enabled / disabled)
All four use the full pipeline: per-field thresholds, keyword boost, and empty-field handling are **ENABLED** in every version. They differ only as:
| version | ROI geometry | weight calibration | per-field thresholds | keyword boost | empty handling |
|---|---|---|---|---|---|
| **v1** | correct predictions | **OFF (defaults)** | on | on | on |
| **v2** | correct predictions | **ON (grid search)** | on | on | on |
| **v3** | **GT (production)** | **ON (grid search)** | on | on | on |
| **v4** | **GT (production)** | **OFF (defaults)** | on | on | on |
(The earlier `../structured_ntp/` run was a direct-primitive prototype: defaults + pred-ROI + containment, with keyword/empty **disabled** — superseded by v1 here, which reproduces its catch.)

## RESULTS — present-field population (the honest spatial-detectability numbers)
{PRES}

## RESULTS — full population (includes absent-field hallucinations; catch is inflated)
{FULL}
*(↑ higher better, ↓ lower better. Correctness is a label on identical accept/route decisions.)*

## Key findings
1. **Containment → exact is the dominant driver of catch** (present-field): ~1.00 → ~0.54–0.61. The ~40 points lost are **in-place value errors** (right location, wrong value) that a spatial verifier cannot catch by design — the real **detectability frontier** for the structured channel.
2. **Weight calibration gives a modest lift** under exact (pred-ROI 0.535→0.612; GT-ROI 0.595→0.614) and lowers false-alarm. It helps approach the ceiling; it does not raise the ceiling.
3. **Prediction-ROI ≥ GT-ROI** for verifying this extractor: v2 vs v3 (exact) catch ties (~0.61) but pred-ROI has ~half the false-alarm (0.045 vs 0.087) and higher accuracy (0.920 vs 0.883). Learning the region from the extractor's own correct outputs aligns it to that extractor. (GT-ROI remains the more general/principled choice; v3 is the production headline.)
4. **Absent-field hallucinations are a separate, trivially-caught error type** (≈100% routed; no ROI exists). They inflate full-population catch to ~0.81 and should be reported separately, not as the spatial result.
5. **Best overall config = v2** (pred-ROI + calibration): highest accuracy, lowest false-alarm, catch tied with production.
6. **Document-level cost**: with ~10% field-level routing (present, exact) and ~98% of docs holding ≥1 exact-error, "accept iff all units accept" routes a large majority of documents — the honest usability cost on this clean/rigid dataset.

## Directory map (under experiments/)
```
structured_ntp/                 # v0 prototype: direct primitives, defaults, containment (superseded)
  inputs/fatura_ocr/            #   10k OCR token files (0-1000 space) — reused by v2
  splits/fatura_split.json      #   per-template 70/30 split (seed 42) — reused by v2
structured_ntp/fatura/              # THIS experiment
  gt_clean/                     # Task-2 cleaned GT + cleaning_quality.json
  task1_predroi_containment/    # v2 containment  (decisions.jsonl, roi_models/, datasets/, analysis/, paper/)
  task3a_predroi_exact/         # v2 exact
  task3b_gt_endtoend_exact/     # v3 exact (production)
  matrix/v1_pred_nocalib/       # v1 (both labels)
  matrix/v3cont_gt_calib_contain/   # v3 containment
  matrix/v4_gt_nocalib/         # v4 (both labels)
  matrix/v2clean_exact|contain/ # validation: cleaned-input reruns (0 diffs vs filtered)
  paper/matrix_table.md         # the 8-row present table
  paper/comparison.md           # earlier cross-task summary
  paper/STRUCTURED_EXPERIMENT.md# THIS document
  scripts/                      # clean_gt.py, run_matrix.py, analyze_matrix.py, compare_clean.py, doc_structured.py
```

## Reproduce
```
PY=/Users/rajeshgupta/Git_Clones/NTP/NTP/venv/bin/python
$PY scripts/clean_gt.py
# v2 (both labels): calibration on
$PY scripts/run_matrix.py --geom pred --corr exact       --calib on  --name task3a_predroi_exact   # (or reuse task dirs)
$PY scripts/run_matrix.py --geom pred --corr containment --calib on  --name task1_predroi_containment
# v1 / v3-containment / v4
$PY scripts/run_matrix.py --geom pred --corr containment --calib off --name v1_pred_nocalib
$PY scripts/run_matrix.py --geom gt   --corr containment --calib on  --name v3cont_gt_calib_contain
$PY scripts/run_matrix.py --geom gt   --corr exact       --calib off --name v4_gt_nocalib
$PY scripts/doc_structured.py   # regenerate this doc + tables
# validation (optional): identical present-field results from cleaned input
$PY scripts/run_matrix.py --geom pred --corr exact --calib on --present-only --name v2clean_exact
$PY scripts/compare_clean.py
```

## Data provenance
Predictions + GT: `experiments/results/fatura_results/` (extraction_results_fatura.json, ground_truth_fatura.json — 10k docs, NuExtract-3). OCR: FATURA `layoutlm_HF_format` → `structured_ntp/inputs/fatura_ocr/`.
Validation: `compare_clean.py` → 0/31,378 (exact) and 0/29,199 (containment) decision differences between cleaned-input reruns and present-field-filtered originals.
"""
(V2/"paper"/"STRUCTURED_EXPERIMENT.md").write_text(doc)
print("PRESENT TABLE:\n"+PRES+"\n\nFULL TABLE:\n"+FULL)
print(f"\n-> {V2/'paper'/'STRUCTURED_EXPERIMENT.md'}")
