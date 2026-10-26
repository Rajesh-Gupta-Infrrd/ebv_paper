"""
Dataset adapters: turn a raw public dataset on disk into a uniform stream of
documents for the extractor, plus the field schema and (for later labelling) the
ground-truth values.

Each `Document` has:
  doc_id       : stable id (output JSON key + resume key)
  images       : page-image paths (used when input_mode == "image")
  text         : document text   (used when input_mode == "text")
  ground_truth : {field: gt_value_or_None}   (NOT given to the model; for labelling)

Each adapter exposes: field_schema(), documents(limit), .doc_type, .input_mode.
Schemas are derived from the dataset's own ground truth (data-driven, like the NER
harness reading fields from GT), not hardcoded.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

csv.field_size_limit(10**7)  # RealKIE cells are large


@dataclass
class Document:
    doc_id: str
    images: list[Path] = field(default_factory=list)
    text: str | None = None
    ground_truth: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# FATURA (structured / ROI) — single-page synthetic invoices
# --------------------------------------------------------------------------- #
class FaturaAdapter:
    def __init__(self, cfg: dict):
        self.name = cfg["name"]
        self.doc_type = cfg["doc_type"]
        self.input_mode = cfg["input_mode"]
        self.root = Path(cfg["root"])
        self.images_dir = self.root / cfg["images_subdir"]
        self.annot_dir = self.root / cfg["annotations_subdir"]
        self.blocklist = set(cfg.get("field_blocklist", []))
        self.sample_templates = cfg.get("sample_templates")
        self.sample_per_template = cfg.get("sample_per_template", 100)
        self._schema: list[str] | None = None

    def _iter_stems(self, limit: int | None) -> Iterator[str]:
        count = 0
        for tmpl in self.sample_templates:
            picked = 0
            candidates = sorted(
                self.images_dir.glob(f"Template{tmpl}_Instance*.jpg"),
                key=lambda p: int(p.stem.split("Instance")[-1]),
            )
            for img in candidates:
                if picked >= self.sample_per_template:
                    break
                if not (self.annot_dir / f"{img.stem}.json").exists():
                    continue
                yield img.stem
                picked += 1
                count += 1
                if limit and count >= limit:
                    return

    def _load_annot(self, stem: str) -> dict:
        try:
            return json.loads((self.annot_dir / f"{stem}.json").read_text())
        except Exception:
            return {}

    def _schema_stems(self, per_template: int = 5) -> Iterator[str]:
        """A few instances from EVERY template, for a complete field-schema union.
        Independent of sample_per_template, so the schema can't collapse to one
        template when each template fills its full quota (e.g. the 10k full run)."""
        for tmpl in self.sample_templates:
            picked = 0
            for img in sorted(
                self.images_dir.glob(f"Template{tmpl}_Instance*.jpg"),
                key=lambda p: int(p.stem.split("Instance")[-1]),
            ):
                if picked >= per_template:
                    break
                if (self.annot_dir / f"{img.stem}.json").exists():
                    yield img.stem
                    picked += 1

    def field_schema(self) -> list[str]:
        if self._schema is None:
            seen: dict[str, None] = {}
            for stem in self._schema_stems():
                for k, v in self._load_annot(stem).items():
                    if k not in self.blocklist and isinstance(v, dict) and v.get("text"):
                        seen.setdefault(k, None)
            self._schema = sorted(seen.keys())  # deterministic order across runs
        return self._schema

    def documents(self, limit: int | None = None) -> Iterator[Document]:
        schema = self.field_schema()
        for stem in self._iter_stems(limit):
            annot = self._load_annot(stem)
            gt = {f: (annot.get(f, {}).get("text") if isinstance(annot.get(f), dict) else None)
                  for f in schema}
            yield Document(
                doc_id=stem,
                images=[self.images_dir / f"{stem}.jpg"],
                ground_truth=gt,
                meta={"template": stem.split("_Instance")[0]},
            )


# --------------------------------------------------------------------------- #
# RealKIE (unstructured / Signal) — multi-page real documents.
# One adapter for ALL RealKIE domains (FCC, Charities, NDA, …): identical on-disk
# layout (train.csv with labels/text/image_files/original_filename; images/<id>/page_N.png).
# --------------------------------------------------------------------------- #
class RealKieAdapter:
    def __init__(self, cfg: dict):
        self.name = cfg["name"]
        self.doc_type = cfg["doc_type"]
        self.input_mode = cfg["input_mode"]
        self.root = Path(cfg["root"])
        self.csv_path = self.root / cfg["split_csv"]
        self.max_pages = cfg.get("max_pages", 8)
        self._schema: list[str] | None = None

    def _rows(self) -> Iterator[dict]:
        with open(self.csv_path, newline="") as f:
            yield from csv.DictReader(f)

    @staticmethod
    def _labels(row: dict) -> list[dict]:
        try:
            return json.loads(row.get("labels") or "[]")
        except Exception:
            return []

    def field_schema(self) -> list[str]:
        if self._schema is None:
            names: dict[str, None] = {}
            for row in self._rows():
                for span in self._labels(row):
                    if span.get("label"):
                        names.setdefault(span["label"], None)
            self._schema = list(names.keys())
        return self._schema

    def _ground_truth(self, labels: list[dict], schema: list[str]) -> dict[str, Any]:
        gt: dict[str, list[str]] = {f: [] for f in schema}
        for span in labels:
            if span.get("label") in gt and span.get("text"):
                gt[span["label"]].append(span["text"])
        return {f: (vals[0] if len(vals) == 1 else (vals or None)) for f, vals in gt.items()}

    def _image_paths(self, row: dict) -> list[Path]:
        try:
            rels = json.loads(row.get("image_files") or "[]")
        except Exception:
            rels = []
        out = []
        for rel in rels[: self.max_pages]:
            # stored as "<dataset>/images/<docid>/page_N.png" → strip the leading
            # dataset component (same convention across all RealKIE domains).
            p = self.root / Path(*Path(rel).parts[1:])
            if p.exists():
                out.append(p)
        return out

    def documents(self, limit: int | None = None) -> Iterator[Document]:
        schema = self.field_schema()
        # Guarantee unique doc_ids. Most RealKIE domains have one row per document,
        # so this is a no-op there. S-1 is pre-split into PAGE segments that can share
        # one original_filename; without this the second page would overwrite the first
        # in the output dict (keyed by doc_id) and corrupt --resume. First occurrence
        # keeps the bare stem (unchanged behaviour); later ones get a deterministic
        # `__pN` suffix so the run stays reproducible/resumable.
        seen: dict[str, int] = {}
        for i, row in enumerate(self._rows()):
            if limit and i >= limit:
                return
            labels = self._labels(row)
            base = Path(row.get("original_filename") or f"doc_{i}").stem
            n = seen.get(base, 0)
            seen[base] = n + 1
            doc_id = base if n == 0 else f"{base}__p{n}"
            yield Document(
                doc_id=doc_id,
                images=self._image_paths(row),
                text=row.get("text") or None,
                ground_truth=self._ground_truth(labels, schema),
            )


# --------------------------------------------------------------------------- #
# VRDU – Registration Forms / FARA (structured / ROI) — real templatic forms
# --------------------------------------------------------------------------- #
class VrduAdapter:
    """Reads VRDU's `dataset.jsonl` (one entry per doc: filename, ocr, annotations).
    GT is taken from `annotations` ([entity_name, [[text, bbox, spans], …]]). Page
    images are the PNGs `prep_vrdu.py` renders from the PDFs → images/<stem>/page_N.png.
    Field schema is the data-driven union of annotation entity names."""

    def __init__(self, cfg: dict):
        self.name = cfg["name"]
        self.doc_type = cfg["doc_type"]
        self.input_mode = cfg["input_mode"]
        self.root = Path(cfg["root"])
        self.jsonl = self.root / cfg.get("dataset_jsonl", "main/dataset.jsonl")
        self.images_dir = self.root / cfg.get("images_subdir", "images")
        self.max_pages = cfg.get("max_pages", 8)
        self._schema: list[str] | None = None

    def _entries(self) -> Iterator[dict]:
        if not self.jsonl.exists():
            raise FileNotFoundError(
                f"{self.jsonl} not found — run `python prep_vrdu.py` first "
                f"(it gunzips dataset.jsonl.gz and renders page images)."
            )
        with open(self.jsonl) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue

    @staticmethod
    def _ann_value(occurrences: Any) -> Any:
        """annotations entry value = [[text, bbox, spans], …]; GT = the text(s)."""
        texts: list[str] = []
        for occ in occurrences or []:
            if isinstance(occ, (list, tuple)) and occ and occ[0] is not None:
                t = str(occ[0]).strip()
                if t:
                    texts.append(t)
        if not texts:
            return None
        return texts[0] if len(texts) == 1 else texts

    def field_schema(self) -> list[str]:
        if self._schema is None:
            seen: dict[str, None] = {}
            for e in self._entries():
                for pair in e.get("annotations", []):
                    if isinstance(pair, (list, tuple)) and pair and pair[0]:
                        seen.setdefault(str(pair[0]), None)
            self._schema = sorted(seen.keys())
        return self._schema

    def _images(self, stem: str) -> list[Path]:
        d = self.images_dir / stem
        if not d.is_dir():
            return []
        pages = sorted(
            d.glob("page_*.png"),
            key=lambda p: int(p.stem.split("_")[-1]) if p.stem.split("_")[-1].isdigit() else 0,
        )
        return pages[: self.max_pages]

    def documents(self, limit: int | None = None) -> Iterator[Document]:
        schema = self.field_schema()
        count = 0
        for e in self._entries():
            if limit and count >= limit:
                return
            fn = e.get("filename") or ""
            stem = Path(fn).stem
            ann = {str(pair[0]): self._ann_value(pair[1])
                   for pair in e.get("annotations", [])
                   if isinstance(pair, (list, tuple)) and len(pair) >= 2 and pair[0]}
            gt = {f: ann.get(f) for f in schema}
            yield Document(
                doc_id=stem,
                images=self._images(stem),   # empty → run_extraction records a clear per-doc error
                text=None,
                ground_truth=gt,
                meta={"filename": fn},
            )
            count += 1


def get_adapter(cfg: dict):
    if cfg["name"] == "fatura":
        return FaturaAdapter(cfg)
    if cfg["name"] in ("realkie_fcc", "realkie_charities", "realkie_nda", "realkie_s1"):
        return RealKieAdapter(cfg)
    if cfg["name"] == "vrdu":
        return VrduAdapter(cfg)
    raise ValueError(f"unknown dataset {cfg['name']!r}")
