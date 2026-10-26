"""
Central configuration for the EBV extraction experiments.

We run an open-source extractor (NuExtract 3, served with vLLM) over the public
benchmark documents to produce *predictions* that the EBV verifier will later
score. This file holds the model/server settings, generation params, and the
per-dataset adapters' configuration.

Nothing here is secret; paths assume the datasets sit next to this `experiments/`
folder (…/ebv_paper/fatura and …/ebv_paper/realkie_fcc_invoices). Override any of
these with environment variables when running on the remote box.
"""
from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------- #
# Model + vLLM server
# --------------------------------------------------------------------------- #
# NuExtract 3 (Qwen3.5-VL backbone, multimodal). Served OpenAI-compatible via
# `vllm serve`. Use the W4A16 repo instead if you want more VRAM headroom on the A10.
MODEL_ID = os.environ.get("NUEXTRACT_MODEL_ID", "numind/NuExtract3")

SERVER_HOST = os.environ.get("NUEXTRACT_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("NUEXTRACT_PORT", "30000"))
# OpenAI-compatible base URL exposed by `vllm serve`.
SERVER_BASE_URL = os.environ.get(
    "NUEXTRACT_SERVER_URL", f"http://{SERVER_HOST}:{SERVER_PORT}/v1"
)
# vLLM OpenAI server has no key; this is just the dummy the client library expects.
SERVER_API_KEY = os.environ.get("NUEXTRACT_API_KEY", "EMPTY")
REQUEST_TIMEOUT_S = int(os.environ.get("NUEXTRACT_TIMEOUT", "300"))

# Generation params — mirror the proven NER-harness settings (verbatim extraction
# wants low temperature). See extraction/prompt.py for the prompt itself.
GEN_TEMPERATURE = float(os.environ.get("NUEXTRACT_TEMPERATURE", "0.1"))
GEN_TOP_P = float(os.environ.get("NUEXTRACT_TOP_P", "0.9"))
# Output budget. vLLM reserves this up front from max-model-len, so keep it small:
# the extracted JSON (~20 fields) is only a few hundred tokens. (4096 here starved
# the input budget and 400'd every long document.)
GEN_MAX_TOKENS = int(os.environ.get("NUEXTRACT_MAX_TOKENS", "1536"))
# Safety cap on input text length (text mode). ~4 chars/token, so 110k chars ≈ 27.5k
# tokens — fits comfortably under a 32k context with room for prompt + output. Only
# the handful of extreme outliers (e.g. the 158k-char doc) get truncated.
MAX_INPUT_CHARS = int(os.environ.get("NUEXTRACT_MAX_INPUT_CHARS", "110000"))

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent
PAPER_DIR = EXPERIMENTS_DIR.parent                      # …/ebv_paper
RESULTS_DIR = Path(os.environ.get("EBV_RESULTS_DIR", EXPERIMENTS_DIR / "results"))

# Dataset roots (override with env on the remote box if you put them elsewhere).
FATURA_ROOT = Path(os.environ.get("FATURA_ROOT", PAPER_DIR / "experiments" / "datasets" / "fatura"))
REALKIE_FCC_ROOT = Path(
    os.environ.get("REALKIE_FCC_ROOT", PAPER_DIR / "experiments" / "datasets" / "realkie_fcc_invoices")
)
# New generalization datasets (added for the robustness round).
REALKIE_CHARITIES_ROOT = Path(
    os.environ.get("REALKIE_CHARITIES_ROOT", PAPER_DIR / "experiments" / "datasets" / "realkie_charities")
)
REALKIE_NDA_ROOT = Path(
    os.environ.get("REALKIE_NDA_ROOT", PAPER_DIR / "experiments" / "datasets" / "realkie_nda")
)
REALKIE_S1_ROOT = Path(
    os.environ.get("REALKIE_S1_ROOT", PAPER_DIR / "experiments" / "datasets" / "realkie_s1")
)
# VRDU Registration-Forms (FARA) — REAL templatic structured set for the ROI verifier.
VRDU_ROOT = Path(
    os.environ.get("VRDU_ROOT", PAPER_DIR / "experiments" / "datasets" / "vrdu" / "registration-form")
)

# --------------------------------------------------------------------------- #
# Per-dataset config (consumed by extraction/datasets.py)
# --------------------------------------------------------------------------- #
# FATURA (structured / ROI). Single-page synthetic invoices. Default = the FULL
# set: all 50 templates × 200 instances = 10,000 docs. (Extraction is cheap on the
# A10, so we run everything rather than a stratified sample; narrow it with
# `--templates` / `--sample-per-template` on the CLI if you ever want a sample.)
FATURA = {
    "name": "fatura",
    "doc_type": "invoice",
    "root": FATURA_ROOT,
    "images_subdir": "images",                       # <Template_Instance>.jpg
    "annotations_subdir": "Annotations/Original_Format",  # <Template_Instance>.json
    "split_csv": "strat1_train.csv",                 # img_path,annot_path
    "input_mode": "image",                           # ROI needs the page image
    # Field classes in Original_Format that are NOT extractable text fields.
    "field_blocklist": ["TABLE", "LOGO", "OTHER"],
    # Full set: every template (1..50), every instance (200/template).
    "sample_templates": list(range(1, 51)),
    "sample_per_template": 200,
}

# RealKIE – FCC Invoices (unstructured / Signal). Multi-page real invoices.
# Use the WHOLE 370-doc subset (it's small). Signal is text-based, so TEXT input
# is the cheap default; switch input_mode to "image" to feed page PNGs instead.
REALKIE_FCC = {
    "name": "realkie_fcc",
    "doc_type": "fcc_invoice",
    "root": REALKIE_FCC_ROOT,
    "split_csv": "train.csv",        # also val.csv / test.csv; columns incl. labels,text,image_files
    "images_subdir": "images",       # images/<docid>/page_N.png
    "input_mode": "text",            # cheapest; Signal verifier is text-based
    "max_pages": 8,                  # only used when input_mode == "image"
}

# RealKIE – Charities (unstructured / Signal). Long real UK nonprofit reports, 28 fields.
# Same on-disk layout as FCC (files/, images/<id>/page_N.png, ocr/, train.csv with
# labels,text,image_files,original_filename). Text input (Signal is text-based).
REALKIE_CHARITIES = {
    "name": "realkie_charities",
    "doc_type": "charity_report",
    "root": REALKIE_CHARITIES_ROOT,
    "split_csv": "train.csv",
    "images_subdir": "images",
    "input_mode": "text",
    "max_pages": 8,
}

# RealKIE – NDA (unstructured / Signal). Real non-disclosure agreements, near-linear
# text, 3 fields. Same layout as FCC. Different domain → tests Signal generalization.
REALKIE_NDA = {
    "name": "realkie_nda",
    "doc_type": "nda",
    "root": REALKIE_NDA_ROOT,
    "split_csv": "train.csv",
    "images_subdir": "images",
    "input_mode": "text",
    "max_pages": 8,
}

# RealKIE – S-1 (unstructured / Signal). SEC IPO registration filings, 24 fields.
# RealKIE ships these PRE-SPLIT into single pages (~660 words each, 13,079 page
# segments from 322 filings) — so each row is short and clean (no truncation), but
# there are many rows. Same on-disk layout as the other RealKIE domains. New financial
# domain → more pooled Signal instances. Cap the row count with `--limit` (the rows
# are page segments, and many carry no labels), e.g. `--limit 2000`.
REALKIE_S1 = {
    "name": "realkie_s1",
    "doc_type": "s1_filing",
    "root": REALKIE_S1_ROOT,
    "split_csv": "train.csv",
    "images_subdir": "images",
    "input_mode": "text",
    "max_pages": 8,
}

# VRDU Registration-Forms / FARA (structured / ROI). 1,915 REAL docs, 3 templates,
# 6 fields, per-field bounding boxes. Ships PDFs + dataset.jsonl (OCR+annotations);
# `prep_vrdu.py` renders page PNGs to images/<stem>/page_N.png for NuExtract image mode.
VRDU = {
    "name": "vrdu",
    "doc_type": "registration_form",
    "root": VRDU_ROOT,
    "dataset_jsonl": "main/dataset.jsonl",   # produced by `gzip -d main/dataset.jsonl.gz`
    "images_subdir": "images",               # rendered by prep_vrdu.py
    "input_mode": "image",                   # ROI is spatial → feed the page image (like FATURA)
    "max_pages": 8,
}

DATASETS = {
    "fatura": FATURA,
    "realkie_fcc": REALKIE_FCC,
    "realkie_charities": REALKIE_CHARITIES,
    "realkie_nda": REALKIE_NDA,
    "realkie_s1": REALKIE_S1,
    "vrdu": VRDU,
}
