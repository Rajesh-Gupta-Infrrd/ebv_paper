#!/usr/bin/env python3
"""NuExtract-3 (fields) over the ROCKET PDFs — runs on the A10 against a local vLLM server.

Reuses the proven extractor (../extraction/extractor.py + config.py). For each PDF it
renders page images (PyMuPDF) and asks NuExtract for the per-type field list
(datasets/rocket/<type>/field_list.json). Writes one prediction file per document:

    datasets/rocket/<type>/nuextract/<requestId>.json
      { requestId, docType, extracted: {field: value}, metrics, n_pages }

Ground truth stays in the DB (correctedValue) and is joined locally at verification time.

Prereqs on the A10 (see setup_rocket_gpu.sh):
  source nuextract-venv/bin/activate
  bash ../extraction/serve_nuextract.sh &      # vLLM OpenAI server on :30000
  python run_rocket_nuextract.py               # --types URLA,CD_tables  --limit N
"""
from __future__ import annotations
import argparse, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "extraction"))   # config.py + extractor.py
import config, extractor                                # noqa: E402
try:
    import pymupdf as fitz                              # PyMuPDF (new name, no deprecation warning)
except ImportError:
    import fitz                                         # noqa: E402

ROOT = Path(os.environ.get("ROCKET_ROOT", HERE.parent / "datasets" / "rocket"))
DOC_TYPES = {
    "URLA": "loan_application", "CD_tables": "closing_disclosure",
    "AUS_DU": "underwriting_findings", "Bank": "bank_statement",
    "CreditReportLender": "credit_report",
}
MAX_PAGES = int(os.environ.get("ROCKET_MAX_PAGES", "8"))
DPI = int(os.environ.get("ROCKET_DPI", "150"))


def rid_of(pdf: Path) -> str:
    return pdf.stem.split("_", 1)[0]     # filename = "<requestId>_<fileName>.pdf"


def render_pages(pdf: Path, tmpdir: Path) -> list[str]:
    doc = fitz.open(pdf); imgs = []
    for i, page in enumerate(doc):
        if i >= MAX_PAGES:
            break
        p = tmpdir / f"{pdf.stem}_p{i}.png"
        page.get_pixmap(dpi=DPI).save(str(p)); imgs.append(str(p))
    doc.close(); return imgs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--types", default=",".join(DOC_TYPES))
    ap.add_argument("--limit", type=int, default=0, help="cap docs per type (0=all)")
    ap.add_argument("--max-workers", type=int, default=int(os.environ.get("ROCKET_WORKERS", "10")),
                    help="concurrent docs sent to vLLM (default 10)")
    a = ap.parse_args()
    if not extractor.health_ok():
        print(f"vLLM server not reachable at {config.SERVER_BASE_URL} — start serve_nuextract.sh first", file=sys.stderr)
        return 1
    for typ in [t.strip() for t in a.types.split(",") if t.strip()]:
        fl = json.load(open(ROOT / typ / "field_list.json"))["fields"]
        outdir = ROOT / typ / "nuextract"; outdir.mkdir(parents=True, exist_ok=True)
        tmp = outdir / "_tmp"; tmp.mkdir(exist_ok=True)
        pdfs = sorted(p for p in (ROOT / typ).glob("*.pdf") if not p.name.startswith("._"))
        if a.limit:
            pdfs = pdfs[: a.limit]
        ok = skip = fail = 0
        todo = []
        for pdf in pdfs:
            dest = outdir / f"{rid_of(pdf)}.json"
            if dest.exists() and dest.stat().st_size > 0:
                skip += 1
            else:
                todo.append(pdf)

        def work(pdf: Path):
            rid = rid_of(pdf); dest = outdir / f"{rid}.json"; imgs = []
            try:
                imgs = render_pages(pdf, tmp)
                extracted, metrics = extractor.extract(fl, images=imgs)
                json.dump({"requestId": rid, "docType": typ, "extracted": extracted,
                           "metrics": metrics, "n_pages": len(imgs)}, open(dest, "w"))
                return rid, None
            except Exception as e:
                return rid, f"{type(e).__name__} {str(e)[:90]}"
            finally:
                for p in imgs:
                    Path(p).unlink(missing_ok=True)

        t0 = time.time()
        with ThreadPoolExecutor(max_workers=a.max_workers) as ex:
            for i, fut in enumerate(as_completed([ex.submit(work, p) for p in todo]), 1):
                rid, err = fut.result()
                if err:
                    fail += 1; print(f"[{typ}] {rid} FAIL {err}", flush=True)
                else:
                    ok += 1
                if i % 10 == 0:
                    print(f"[{typ}] {i}/{len(todo)} ok={ok} fail={fail} {time.time()-t0:.0f}s", flush=True)
        print(f"{typ:20} ok={ok:4} skip={skip:4} fail={fail:3} total={len(pdfs)} fields={len(fl)}", flush=True)
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
