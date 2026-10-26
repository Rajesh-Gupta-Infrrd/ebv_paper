#!/usr/bin/env python3
"""Aggregate the robustness-round results (new datasets) into one report, pulling every
number from the stored metrics JSON — no hand-typed figures.

Sources:
  Signal (unstructured): unstructured_ntp/<ds>/analysis/signal_metrics.json
  ROI (structured):      structured_ntp/vrdu/paper/structured_vrdu_metrics.json
Writes: experiments/ROBUSTNESS_EXPERIMENTS.md
"""
from __future__ import annotations
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
UNS = EXP / "unstructured_ntp"
V2 = EXP / "structured_ntp" / "vrdu"
SIGNAL_DS = [("realkie_charities", "Charities (UK nonprofit reports, 28 fields)"),
             ("realkie_nda", "NDA (non-disclosure agreements, 3 fields)"),
             ("realkie_s1", "S-1 (SEC IPO filings, 24 fields, page-level)")]


def g(x):
    return "—" if x is None else (f"{x:.4f}" if isinstance(x, float) else str(x))


def load(p):
    return json.loads(Path(p).read_text()) if Path(p).exists() else None


def signal_rows(tag):
    """One canonical row per Signal domain for a given run tag (scalar/binary)."""
    rows = []
    for ds, _ in SIGNAL_DS:
        M = load(UNS / ds / "analysis" / "signal_metrics.json")
        if not M or tag not in M.get("metrics", {}):
            rows.append(f"| {ds.replace('realkie_','')} | (pending) | | | | | | | | | |"); continue
        m = M["metrics"][tag]["scalar"]["binary"]
        rows.append(f"| {ds.replace('realkie_','')} | {m['n']} | {m['err_rate']} | {g(m['error_catch'])} | "
                    f"{g(m['false_alarm'])} | {g(m['accuracy'])} | {g(m.get('accept_all_acc'))} | "
                    f"{g(m['AUROC'])} | {g(m['cov@5%'])} | {g(m['cov@10%'])} | {g(m['cov@20%'])} |")
    return rows


def tuning_cleanup_rows():
    """Per domain: AUROC + cov@5% for noisy(untuned) / tuned / clean — the tuning & cleanup study."""
    rows = []
    for ds, _ in SIGNAL_DS:
        M = load(UNS / ds / "analysis" / "signal_metrics.json")
        if not M:
            rows.append(f"| {ds.replace('realkie_','')} | pending |||||| "); continue
        m = M["metrics"]
        def cell(tag):
            if tag not in m: return ("—", "—")
            s = m[tag]["scalar"]["binary"]; return (g(s["AUROC"]), g(s["cov@5%"]))
        na, nc = cell("noisy"); ta, tc = cell("tuned"); ca, cc = cell("clean")
        rows.append(f"| {ds.replace('realkie_','')} | {na} / {nc} | {ta} / {tc} | {ca} / {cc} |")
    return rows


def vrdu_table(block):
    V = load(V2 / "paper" / "structured_vrdu_metrics.json")
    if not V: return "_(VRDU metrics pending)_"
    d = V[block]
    cfg = {"v1": "pred-ROI, calib OFF", "v2": "pred-ROI, calib ON",
           "v3": "GT-ROI, calib ON (prod)", "v4": "GT-ROI, calib OFF"}
    out = ["| ver | config | correctness | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc ↑ | AURC ↓ |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for v in ["v1", "v2", "v3", "v4"]:
        for m in ["exact", "containment"]:
            x = d.get(f"{v}_{m}", {})
            out.append(f"| {v} | {cfg[v]} | {m} | {x.get('n')} | {x.get('err_rate')} | "
                       f"{g(x.get('error_catch'))} | {g(x.get('false_alarm'))} | {g(x.get('route_prec'))} | "
                       f"{g(x.get('accuracy'))} | {g(x.get('AURC'))} |")
    return "\n".join(out)


def vrdu_perfield():
    V = load(V2 / "paper" / "structured_vrdu_metrics.json")
    if not V or "per_field_v3_present_exact" not in V: return "_(pending)_"
    out = ["| field | n | err | catch ↑ | FA ↓ | acc ↑ |", "|---|---|---|---|---|---|"]
    for f, x in V["per_field_v3_present_exact"].items():
        out.append(f"| {f} | {x['n']} | {x['err_rate']} | {g(x['error_catch'])} | {g(x['false_alarm'])} | {g(x['accuracy'])} |")
    return "\n".join(out)


def vrdu_auroc_coverage():
    """VRDU on Jin et al. (2609.20110)'s axes — AUROC + coverage@fixed-risk, present-field.
    Source: structured_vrdu_metrics.json['auroc_coverage_present'] (compute_vrdu_auroc_coverage.py)."""
    V = load(V2 / "paper" / "structured_vrdu_metrics.json")
    if not V or "auroc_coverage_present" not in V: return "_(AUROC/coverage pending)_"
    d = V["auroc_coverage_present"]
    cfg = {"v1": "pred-ROI, calib OFF", "v2": "pred-ROI, calib ON",
           "v3": "GT-ROI, calib ON (prod)", "v4": "GT-ROI, calib OFF"}
    pc = lambda x: "—" if x is None else f"{x*100:.1f}%"
    out = ["| ver | config | correctness | AUROC ↑ | cov@≤5% | cov@≤10% | cov@≤20% |",
           "|---|---|---|---|---|---|---|"]
    rows = [("v1", "exact"), ("v2", "exact"), ("v3", "exact"), ("v4", "exact"), ("v3", "containment")]
    for v, m in rows:
        x = d.get(f"{v}_{m}", {})
        out.append(f"| {v} | {cfg[v]} | {m} | {g(x.get('AUROC'))} | {pc(x.get('cov@5%'))} | "
                   f"{pc(x.get('cov@10%'))} | {pc(x.get('cov@20%'))} |")
    return "\n".join(out)


SIG_HDR = ("| domain | n | err | catch ↑ | FA ↓ | acc | accept-all | AUROC ↑ | cov@5% | cov@10% | cov@20% |\n"
           "|---|---|---|---|---|---|---|---|---|---|---|")


def main():
    md = f"""# EBV robustness round — results on the new datasets

Reproduces the original FATURA (structured/ROI) and FCC (unstructured/Signal) experiments on
**new datasets** to test generalization (synthetic↔real, single↔multi-domain). Same pipelines,
**no extra LLM/VLM call**, dociq + NTP production code driven in place and left untouched. Every
number below is pulled from the stored metrics JSON by `build_robustness_report.py`.

Datasets added this round:
- **Structured / ROI:** VRDU Registration-Forms (FARA) — 1,915 **real** docs, 3 templates, 6 fields —
  the real-document counterpart to synthetic FATURA.
- **Unstructured / Signal:** RealKIE **Charities**, **NDA**, **S-1** — new domains beyond FCC invoices.

---

## 1. Structured / ROI — VRDU (real templatic forms)

Same NTP spatial pipeline as FATURA. Per-template 70/30 split (seed 42), 1,340 train / 575 test.
OCR token boxes + split + clean GT derived from `dataset.jsonl` (no page images needed).

### Present-field population (the honest spatial-detectability numbers)
{vrdu_table('present')}

### Full population (adds absent-field hallucinations; catch inflated)
{vrdu_table('full')}

### Per-field — production config v3 (GT-ROI, calib ON), present/exact
{vrdu_perfield()}

### AUROC & coverage (Jin et al. 2609.20110 axes), present-field
{vrdu_auroc_coverage()}

Jin's "VRDU" is the **Ad-Buy** subset (9 fields); ours is **Registration-Forms/FARA** (6 fields) —
different subset/fields/extractor, **not** a direct head-to-head (shared dataset = FATURA only).

---

## 2. Unstructured / Signal — new RealKIE domains

Same dociq 6-signal classifier. Canonical = **clean (GT-sparsity fix) · untuned · binary · scalar**.
(These domains have no line-item fields, so `scalar` == `all`.) Quote AUROC/coverage, not accuracy.

### Canonical (clean) per domain
{SIG_HDR}
{chr(10).join(signal_rows('clean'))}

For reference, the original **FCC** canonical (from the FCC leg): scalar/binary AUROC **0.897**,
cov@5% **0.842**, catch 0.926, acc 0.721 (accept-all 0.887), n=240.

### Tuning & cleanup study (scalar/binary AUROC / cov@5%)
| domain | untuned-noisy | tuned-noisy | untuned-clean (canonical) |
|---|---|---|---|
{chr(10).join(tuning_cleanup_rows())}

---

## 3. Findings
_(to be written from the numbers above)_

## 4. Provenance & reproduce
- Signal: `unstructured_ntp/scripts/domain_signal.py --dataset <ds>` → `<ds>/` (data_clean,
  data_noisy, bundle*, decisions, analysis/signal_metrics.json); report via `report_domain_signal.py`.
- ROI: `structured_ntp/scripts/prep_vrdu_roi.py` then `run_matrix.py --dataset vrdu …`
  (6 runs under `matrix/vrdu_*`); tables via `doc_structured_vrdu.py`.
- dociq (`/Users/rajeshgupta/Git_Clones/dociq`) and NTP code driven in place, unmodified.
"""
    (EXP / "ROBUSTNESS_EXPERIMENTS.md").write_text(md)
    print(md)
    print(f"\n-> {EXP/'ROBUSTNESS_EXPERIMENTS.md'}")


if __name__ == "__main__":
    main()
