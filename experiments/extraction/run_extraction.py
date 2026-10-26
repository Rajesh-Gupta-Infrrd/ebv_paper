#!/usr/bin/env python3
"""
Orchestrator: run NuExtract-3 extraction over a public benchmark and write results
in the NER-harness format the NTP/EBV pipeline expects.

Outputs (under results/):
  extraction_results_<dataset>.json : {doc_id: {MODEL: {doc_type, extracted, metrics}}}
  ground_truth_<dataset>.json       : {doc_id: {field: gt_value}}   (for correct/wrong labelling)
  batch_summary_<dataset>.json      : counts, elapsed, field schema, run config

Usage:
  python run_extraction.py --dataset fatura --max-workers 8 --resume
  python run_extraction.py --dataset realkie_fcc --limit 50
Requires the vLLM server up (see serve_nuextract.sh / setup_and_run.sh).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import config
import datasets as ds
import extractor

MODEL_NAME = config.MODEL_ID.split("/")[-1]  # e.g. "NuExtract3"


def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}


def _extract_one(doc: ds.Document, fields: list[str], input_mode: str):
    if input_mode == "text" and doc.text:
        extracted, metrics = extractor.extract(fields, text=doc.text)
    elif doc.images:
        extracted, metrics = extractor.extract(fields, images=doc.images)
    elif doc.text:  # fallback if images missing
        extracted, metrics = extractor.extract(fields, text=doc.text)
    else:
        extracted, metrics = {}, {"error": "no image or text for document"}
    return doc, extracted, metrics


def main() -> int:
    ap = argparse.ArgumentParser(description="NuExtract-3 extraction over EBV benchmarks")
    ap.add_argument("--dataset", required=True, choices=list(config.DATASETS.keys()))
    ap.add_argument("--limit", type=int, default=None, help="cap number of documents")
    ap.add_argument("--max-workers", type=int, default=8)
    ap.add_argument("--resume", action="store_true", help="skip docs already in results")
    ap.add_argument("--retry-failed", action="store_true",
                    help="with --resume: also reprocess docs whose saved metrics have an error")
    ap.add_argument("--input-mode", choices=["image", "text"], default=None,
                    help="override dataset default (image|text)")
    ap.add_argument("--sample-per-template", type=int, default=None,
                    help="FATURA only: instances per template")
    ap.add_argument("--templates", type=str, default=None,
                    help="FATURA only: comma-separated template numbers, e.g. 1,12,25,37,49")
    ap.add_argument("--output-dir", type=str, default=str(config.RESULTS_DIR))
    args = ap.parse_args()

    cfg = dict(config.DATASETS[args.dataset])
    if args.input_mode:
        cfg["input_mode"] = args.input_mode
    if args.sample_per_template is not None:
        cfg["sample_per_template"] = args.sample_per_template
    if args.templates:
        cfg["sample_templates"] = [int(t) for t in args.templates.split(",") if t.strip()]

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / f"extraction_results_{args.dataset}.json"
    gt_path = out_dir / f"ground_truth_{args.dataset}.json"
    summary_path = out_dir / f"batch_summary_{args.dataset}.json"

    if not extractor.health_ok():
        print(f"ERROR: vLLM server not reachable at {config.SERVER_BASE_URL}. "
              f"Start it (serve_nuextract.sh) first.", file=sys.stderr)
        return 2

    adapter = ds.get_adapter(cfg)
    fields = adapter.field_schema()
    print(f"[{args.dataset}] doc_type={adapter.doc_type} input_mode={cfg['input_mode']} "
          f"fields({len(fields)})={fields}")

    results = _load_json(results_path) if args.resume else {}
    gt_all = _load_json(gt_path) if args.resume else {}
    done = set(results.keys())
    if args.retry_failed:
        failed_ids = {k for k, v in results.items()
                      if ((v.get(MODEL_NAME) or {}).get("metrics") or {}).get("error")}
        done -= failed_ids  # let previously-failed docs be reprocessed (overwritten)
        print(f"[{args.dataset}] --retry-failed: reprocessing {len(failed_ids)} failed docs")

    docs = [d for d in adapter.documents(limit=args.limit) if d.doc_id not in done]
    print(f"[{args.dataset}] {len(docs)} documents to process "
          f"({len(done)} already done){' [resume]' if args.resume else ''}")

    t0 = time.perf_counter()
    completed, failed = 0, 0
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = {ex.submit(_extract_one, d, fields, cfg["input_mode"]): d for d in docs}
        for i, fut in enumerate(as_completed(futs), 1):
            doc, extracted, metrics = fut.result()
            results[doc.doc_id] = {
                MODEL_NAME: {"doc_type": adapter.doc_type,
                             "extracted": extracted, "metrics": metrics}
            }
            gt_all[doc.doc_id] = doc.ground_truth
            if metrics.get("error"):
                failed += 1
            else:
                completed += 1
            if i % 10 == 0 or i == len(docs):  # periodic checkpoint for resumability
                results_path.write_text(json.dumps(results, indent=2))
                gt_path.write_text(json.dumps(gt_all, indent=2))
                print(f"  …{i}/{len(docs)} (ok={completed} failed={failed})")

    results_path.write_text(json.dumps(results, indent=2))
    gt_path.write_text(json.dumps(gt_all, indent=2))

    elapsed = round(time.perf_counter() - t0, 1)
    summary = {
        "dataset": args.dataset,
        "model": config.MODEL_ID,
        "doc_type": adapter.doc_type,
        "input_mode": cfg["input_mode"],
        "field_schema": fields,
        "num_documents": len(results),
        "completed_this_run": completed,
        "failed_this_run": failed,
        "elapsed_s": elapsed,
        "config": {k: (str(v) if isinstance(v, Path) else v)
                   for k, v in cfg.items() if k not in ("root",)},
    }
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"[{args.dataset}] done: {len(results)} docs, {completed} ok / {failed} failed, "
          f"{elapsed}s → {results_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
