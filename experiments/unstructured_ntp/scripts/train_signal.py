#!/usr/bin/env python3
"""
Train the Signal classifier on the FCC TRAIN split by driving dociq's own scripts
in place (cwd = dociq, so its bare imports resolve), using OUR paper venv + OUR data
dirs. dociq repo is never modified; all outputs land under experiments/unstructured_ntp/.

Steps (from the code trace):
  1. score_new_data.py        data/train/invoice.json  -> scored/invoice_improved.json  (computes 6 signals)
  2. run_ntp_direct_classifier.py  scored  -> bundle/   (auto-labels from GT, trains rf+gbm, emits bundle)
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

EBV = next(p for p in Path(__file__).resolve().parents if p.name == "ebv_paper")
UNS = EBV / "experiments" / "unstructured_ntp"
PY = str(UNS / ".venv" / "bin" / "python")
DOCIQ_NTP = Path("/Users/rajeshgupta/Git_Clones/dociq/app/ntp_classifier")
TRAIN_DIR = UNS / "realkie_fcc" / "data" / "train"
SCORED_DIR = UNS / "realkie_fcc" / "scored"


def run(cmd):
    print("+", " ".join(cmd), f"(cwd={DOCIQ_NTP})")
    r = subprocess.run(cmd, cwd=str(DOCIQ_NTP))
    if r.returncode != 0:
        print(f"FAILED (exit {r.returncode})", file=sys.stderr); sys.exit(r.returncode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default=str(UNS / "realkie_fcc" / "bundle"))
    ap.add_argument("--tune", action="store_true", help="run RandomizedSearchCV (omit --skip-tuning)")
    a = ap.parse_args()
    bundle = Path(a.bundle)
    if not bundle.is_absolute():            # anchor under the experiment dir (subprocess cwd=dociq!)
        bundle = UNS / bundle
    SCORED_DIR.mkdir(parents=True, exist_ok=True)
    bundle.mkdir(parents=True, exist_ok=True)
    # 1) compute signals (independent of tuning; reused)
    run([PY, str(DOCIQ_NTP / "score_new_data.py"),
         "--input-dir", str(TRAIN_DIR), "--output-dir", str(SCORED_DIR), "--doc-types", "invoice"])
    # 2) train (auto-label from GT; rf+gbm -> pure sklearn)
    cmd = [PY, str(DOCIQ_NTP / "run_ntp_direct_classifier.py"),
           "--input-dir", str(SCORED_DIR), "--output-dir", str(bundle),
           "--auto-signals", "--models", "rf", "gbm", "--doc-types", "invoice"]
    if not a.tune:
        cmd.append("--skip-tuning")
    run(cmd)
    print(f"\nbundle -> {bundle}  (tuning={'ON' if a.tune else 'OFF'})")
    for p in sorted(bundle.rglob("*")):
        if p.is_file():
            print("  ", p.relative_to(bundle))


if __name__ == "__main__":
    main()
