#!/usr/bin/env python3
"""MinerU (tables) over the ROCKET PDFs — runs on the A10. vLLM engine, ONE model load.

Client for the SAME server DocAI parse uses (mineru_extract_server.py, vllm-async-engine,
micro-batching, POST /extract). run_rocket.sh starts the server in the top tmux pane.

Writes one FULL output file per document (resumable — existing files are skipped):
    datasets/rocket/<type>/mineru/<requestId>.json
      { requestId, docType, model_id, dpi, n_pages, markdown,
        pages:[{page_idx, content_list:[all blocks], markdown}],
        tables:[{page_idx, table_html}] }   # tables = convenience subset

Post-processing (layout/refinement) + Table-Trust scoring run LOCALLY afterwards.

    python run_rocket_mineru.py [--types CD_tables,URLA] [--limit N]
"""
from __future__ import annotations
import argparse, json, os, sys, time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # noqa: F401
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("ROCKET_ROOT", HERE.parent / "datasets" / "rocket"))
TYPES = ["URLA", "CD_tables", "AUS_DU", "Bank", "CreditReportLender"]
MODEL_ID = os.environ.get("MINERU_MODEL_ID", "opendatalab/MinerU2.5-Pro-2605-1.2B")
SERVER = os.environ.get("MINERU_SERVER_URL", f"http://127.0.0.1:{os.environ.get('MINERU_PORT', '30001')}")
DPI = int(os.environ.get("ROCKET_MINERU_DPI", "200"))
MAX_PAGES = int(os.environ.get("ROCKET_MAX_PAGES", "8"))


def rid_of(pdf: Path) -> str:
    return pdf.stem.split("_", 1)[0]     # filename = "<requestId>_<fileName>.pdf"


def render(pdf: Path) -> list[Image.Image]:
    doc = fitz.open(pdf); out = []
    for i, page in enumerate(doc):
        if i >= MAX_PAGES:
            break
        pix = page.get_pixmap(matrix=fitz.Matrix(DPI / 72, DPI / 72), alpha=False)
        out.append(Image.open(BytesIO(pix.tobytes("png"))).convert("RGB"))
    doc.close(); return out


def table_html(block: dict) -> str:
    return block.get("content") or block.get("table_body") or block.get("html") or ""


def _safe_render(pdf: Path):
    try:
        return render(pdf)
    except Exception:
        return None


def extract_page(img: Image.Image, tmpdir: Path, tag: str) -> list[dict]:
    """POST one page image to the parse-style MinerU server (/extract) -> content_list."""
    path = tmpdir / f"{tag}.png"
    img.save(path)
    try:
        r = requests.post(f"{SERVER}/extract", json={"image_path": str(path), "image_analysis": False}, timeout=600)
        r.raise_for_status()
        return r.json()["content_list"]
    finally:
        path.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--types", default=",".join(TYPES))
    ap.add_argument("--limit", type=int, default=0, help="cap docs per type (smoke test)")
    ap.add_argument("--max-workers", type=int, default=int(os.environ.get("ROCKET_MINERU_WORKERS", "8")),
                    help="docs batched per vLLM call + parallel PDF rendering (default 8)")
    a = ap.parse_args()
    types = [t.strip() for t in a.types.split(",") if t.strip()]

    requests.get(f"{SERVER}/health", timeout=10).raise_for_status()
    print(f"MinerU server OK at {SERVER}", flush=True)
    tmpdir = ROOT / "_mineru_tmp"; tmpdir.mkdir(exist_ok=True)
    ntab_all = 0
    for typ in types:
        pdfs = sorted(p for p in (ROOT / typ).glob("*.pdf") if not p.name.startswith("._"))
        if a.limit:
            pdfs = pdfs[: a.limit]
        outdir = ROOT / typ / "mineru"; outdir.mkdir(parents=True, exist_ok=True)
        ok = skip = fail = ntab = 0; t0 = time.time()
        todo = []
        for pdf in pdfs:
            dest = outdir / f"{rid_of(pdf)}.json"
            if dest.exists() and dest.stat().st_size > 0:
                skip += 1
            else:
                todo.append(pdf)

        def save(pdf: Path, imgs, pages) -> int:
            if sum(len(b) for b in pages) == 0:   # model produced nothing -> don't mark done
                raise ValueError("empty MinerU output (0 blocks)")
            tables = [{"page_idx": pi, "table_html": table_html(b)}
                      for pi, blocks in enumerate(pages) for b in blocks
                      if b.get("type") == "table" and table_html(b)]
            try:
                from mineru_vl_utils.post_process import json2md
                md_pages = [json2md(blocks) for blocks in pages]
            except Exception:
                md_pages = []
            rid = rid_of(pdf)
            # FULL MinerU output (every block type: text/title/table/image/equation/...) like the OCR stage
            json.dump({"requestId": rid, "docType": typ, "model_id": MODEL_ID, "dpi": DPI,
                       "n_pages": len(imgs), "tables": tables,
                       "pages": [{"page_idx": pi, "content_list": blocks,
                                  "markdown": md_pages[pi] if pi < len(md_pages) else ""}
                                 for pi, blocks in enumerate(pages)],
                       "markdown": "\n\n".join(f"<!-- page {i+1} -->\n{m}" for i, m in enumerate(md_pages))},
                      open(outdir / f"{rid}.json", "w"), default=str, ensure_ascii=False)
            return len(tables)

        def work(pdf: Path):
            imgs = render(pdf)
            with ThreadPoolExecutor(max_workers=4) as pex:   # pages of one doc in parallel -> server micro-batches
                pages = list(pex.map(lambda t: extract_page(t[1], tmpdir, f"{pdf.stem[:40]}_{t[0]}"), enumerate(imgs)))
            return pdf, imgs, pages

        W = max(1, a.max_workers)
        with ThreadPoolExecutor(max_workers=W) as ex:
            futs = {ex.submit(work, p): p for p in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                p = futs[fut]
                try:
                    pdf, imgs, pages = fut.result()
                    ntab += save(pdf, imgs, pages); ok += 1
                except Exception as e:
                    fail += 1; print(f"[{typ}] {rid_of(p)} FAIL {type(e).__name__} {str(e)[:90]}", flush=True)
                if i % 5 == 0 or i == len(todo):
                    print(f"[{typ}] {i}/{len(todo)}  ok={ok} fail={fail} tables={ntab}  {time.time()-t0:.0f}s", flush=True)
        ntab_all += ntab
        print(f"{typ:20} ok={ok:4} skip={skip:4} fail={fail:3} total={len(pdfs)} tables={ntab}", flush=True)
    print(f"total tables extracted={ntab_all}")
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
