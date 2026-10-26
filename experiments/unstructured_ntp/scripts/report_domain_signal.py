#!/usr/bin/env python3
"""Render a per-domain Signal results MD from <dataset>/analysis/signal_metrics.json
(produced by domain_signal.py). Mirrors the FCC paper/UNSTRUCTURED_EXPERIMENT.md tables:
tuning comparison (§4a), before/after-clean (§5), canonical clean (§7), per-signal (§7a)."""
from __future__ import annotations
import argparse, json
from pathlib import Path

EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
UNS = EBV / "experiments" / "unstructured_ntp"


def g(x):
    return "—" if x is None else (f"{x:.4f}" if isinstance(x, float) else str(x))


def row(tag, m):
    return (f"| {tag} | {m['n']} | {m['err_rate']} | {g(m['error_catch'])} | {g(m['false_alarm'])} | "
            f"{g(m['route_prec'])} | {g(m['accuracy'])} | {g(m.get('accept_all_acc'))} | "
            f"{g(m['AUROC'])} | {g(m['cov@5%'])} | {g(m['cov@10%'])} | {g(m['cov@20%'])} |")


HDR = ("| run · pop · mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |\n"
       "|---|---|---|---|---|---|---|---|---|---|---|---|")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dataset", required=True); a = ap.parse_args()
    root = UNS / a.dataset
    M = json.loads((root / "analysis" / "signal_metrics.json").read_text())
    m = M["metrics"]; splits = M.get("splits", {})
    has_lineitem = any(splits.get(k, {}).get("n_lineitem", 0) for k in splits)

    def block(tags, pops=("scalar", "all"), modes=("binary", "3tier")):
        out = [HDR]
        for tag in tags:
            if tag not in m: continue
            for pop in pops:
                for mode in modes:
                    out.append(row(f"{tag} · {pop} · {mode}", m[tag][pop][mode]))
        return "\n".join(out)

    canonical = m.get("clean", {})
    cl_sc = canonical.get("scalar", {}).get("binary", {})
    md = [f"# Signal (unstructured) NTP — {a.dataset} robustness results", "",
          f"doc_type = `{M['doc_type']}`. Same dociq Signal classifier + 6 text signals as the FCC leg "
          "(no extra model call), driven in place; dociq untouched. Built with the GT-sparsity cleanup "
          "(`clean`, canonical) and the pre-fix labels (`noisy`) + a tuned (RandomizedSearchCV) variant.",
          ""]
    if not has_lineitem:
        md.append("> This domain has **no line-item/tabular fields** → `scalar` == `all` population.\n")
    md += ["## TL;DR (canonical = clean · untuned · binary · scalar)",
           f"- AUROC **{g(cl_sc.get('AUROC'))}**, accuracy {g(cl_sc.get('accuracy'))} "
           f"(accept-all {g(cl_sc.get('accept_all_acc'))}), error-catch {g(cl_sc.get('error_catch'))}, "
           f"cov@5% {g(cl_sc.get('cov@5%'))} (n={cl_sc.get('n')}, err={cl_sc.get('err_rate')}).",
           "- Quote the **AUROC/coverage** (capability), not accuracy (see the FCC doc §6 for why).", ""]

    md += ["## 1. Canonical (clean) — all populations/modes", block(["clean"]), ""]
    md += ["## 2. Tuning: untuned(noisy) vs tuned(noisy)", block(["noisy", "tuned"]), "",
           "_Tuning = RandomizedSearchCV only (same data/signals/algorithm)._", ""]
    md += ["## 3. Before vs after the GT-sparsity cleanup (noisy → clean, untuned)",
           block(["noisy", "clean"]), ""]

    # per-signal separation (clean)
    ps = canonical.get("per_signal_mean", {})
    md += ["## 4. Per-signal separation (clean; mean signal value, correct vs wrong)",
           "| signal | mean(correct) | mean(wrong) |", "|---|---|---|"]
    for s, v in ps.items():
        md.append(f"| {s} | {g(v.get('mean_correct'))} | {g(v.get('mean_wrong'))} |")
    suf = canonical.get("sufficiency", {})
    md += ["", f"Sufficiency (clean): empty_prior_applied={suf.get('empty_prior_applied')}, "
           f"gated={suf.get('gated')}, 3-tier={suf.get('tier3_breakdown')}", ""]

    sc = splits.get("clean", {})
    md += ["## 5. Data & split",
           f"- clean: {sc.get('n_docs')} docs ({sc.get('n_train')} train / {sc.get('n_test')} test), "
           f"{sc.get('n_field_instances')} field instances (scalar {sc.get('n_scalar')}, "
           f"lineitem {sc.get('n_lineitem')}), dropped_unlabelled={sc.get('dropped_unlabelled')}, "
           f"skipped={sc.get('skipped')}.",
           f"- Provenance: predictions+GT `experiments/results/{a.dataset}_results/`, "
           f"text `{a.dataset}/train.csv`. Decisions: `{a.dataset}/decisions/`.", ""]

    (root / "paper").mkdir(exist_ok=True)
    (root / "paper" / f"UNSTRUCTURED_{a.dataset}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:14]))
    print(f"\n-> {root/'paper'/f'UNSTRUCTURED_{a.dataset}.md'}")


if __name__ == "__main__":
    main()
