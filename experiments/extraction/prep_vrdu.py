#!/usr/bin/env python3
"""
Prepare VRDU Registration-Forms (FARA) for extraction:
  1. gunzip  main/dataset.jsonl.gz  ->  main/dataset.jsonl   (if not already done)
  2. render each PDF in main/pdfs/   ->  images/<stem>/page_N.png   (poppler `pdftoppm`)

Idempotent: skips a doc whose image dir already has page_*.png. Run once after the
git sparse-checkout of registration-form/. Fails loudly if poppler or the PDFs are
missing, so extraction never starts against empty data.

Usage:  python prep_vrdu.py [--root <registration-form dir>] [--dpi 150] [--limit N]
"""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import subprocess
import sys
from pathlib import Path

import config


def _gunzip(root: Path) -> Path:
    jsonl = root / "main" / "dataset.jsonl"
    gz = root / "main" / "dataset.jsonl.gz"
    if jsonl.exists():
        return jsonl
    if not gz.exists():
        sys.exit(f"ERROR: neither {jsonl} nor {gz} exists — did the VRDU checkout run?")
    print(f"gunzip {gz} -> {jsonl}")
    with gzip.open(gz, "rb") as fi, open(jsonl, "wb") as fo:
        shutil.copyfileobj(fi, fo)
    return jsonl


def _render(pdf: Path, out_dir: Path, dpi: int) -> int:
    """Render a PDF to out_dir/page_0.png, page_1.png, … Returns #pages written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # pdftoppm writes <prefix>-1.png, <prefix>-2.png … ; we rename to page_0, page_1, …
    prefix = out_dir / "p"
    try:
        subprocess.run(
            ["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"  WARN render failed for {pdf.name}: {e.stderr.decode('utf-8','ignore')[:200]}")
        return 0
    pages = sorted(out_dir.glob("p-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
    for i, p in enumerate(pages):
        p.rename(out_dir / f"page_{i}.png")
    return len(pages)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(config.VRDU_ROOT))
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    root = Path(a.root)

    if not shutil.which("pdftoppm"):
        sys.exit("ERROR: `pdftoppm` not found. Install poppler-utils "
                 "(apt-get install -y poppler-utils).")
    pdfs_dir = root / "main" / "pdfs"
    if not pdfs_dir.is_dir() or not any(pdfs_dir.glob("*.pdf")):
        sys.exit(f"ERROR: no PDFs under {pdfs_dir} — check the VRDU sparse-checkout.")

    jsonl = _gunzip(root)
    images_root = root / "images"
    images_root.mkdir(exist_ok=True)

    done = rendered = missing = skipped = 0
    with open(jsonl) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if a.limit and done >= a.limit:
                break
            done += 1
            fn = e.get("filename") or ""
            if not fn:
                continue
            stem = Path(fn).stem
            out_dir = images_root / stem
            if out_dir.is_dir() and any(out_dir.glob("page_*.png")):
                skipped += 1
                continue
            pdf = pdfs_dir / fn
            if not pdf.exists():                    # try common suffixes
                pdf = pdfs_dir / f"{stem}.pdf"
            if not pdf.exists():
                missing += 1
                continue
            if _render(pdf, out_dir, a.dpi) > 0:
                rendered += 1
            if (rendered + skipped) % 200 == 0:
                print(f"  …{rendered} rendered, {skipped} already present, {missing} pdf-missing")

    print(f"VRDU prep done: {done} entries | {rendered} rendered | {skipped} skipped "
          f"| {missing} pdf-missing -> {images_root}")
    if rendered == 0 and skipped == 0:
        sys.exit("ERROR: rendered 0 images — extraction would fail. Check poppler + PDFs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
