# EBV Experiments — Extraction (Stage 1)

Runs an open-source extractor (**NuExtract 3**, served with **vLLM**) over the public
benchmark documents to produce the *predictions* that the EBV verifier scores. The
extractor is only the **source of realistic errors** — not the thing we evaluate — so
we use a free, self-hostable model (NuExtract 3 matched your product's Gemini extractor
in prior benchmarking) instead of a paid API.

Pipeline (this folder covers **Stage 1 only**):
```
Stage 1  extract        docs → NuExtract3 → predictions          ← THIS CODE
Stage 2  label          prediction vs GT → correct/wrong (c)     (next)
Stage 3  verify + score run EBV verifier → accept/route, risk-coverage, detectability  (next)
```

## Layout
```
experiments/
├── config.py                 # model id, vLLM server url, paths, per-dataset config
├── requirements.txt          # vllm, Pillow, requests
├── serve_nuextract.sh        # `vllm serve numind/NuExtract3` (A10 settings)
├── setup_and_run.sh          # install | start | all | serve  (deps, datasets, tmux, health-wait, run)
├── extractor.py              # prompt + vLLM client + JSON parsing (one module)
├── datasets.py               # FATURA + RealKIE (FCC/Charities/NDA) + VRDU adapters
├── prep_vrdu.py              # VRDU only: gunzip dataset.jsonl + render page PNGs (pdftoppm)
├── run_extraction.py         # orchestrator: dataset → predictions JSON (resumable)
└── results/                  # outputs (created at run time)
```

## Quick start (remote A10)
```bash
# on the GPU box, from this experiments/ dir:
./setup_and_run.sh install                       # system deps + venv (poppler, p7zip, git…)
# then run each dataset in its own tmux session (each downloads ONLY its own data):
DATASET=vrdu              ./setup_and_run.sh start   # real templatic ROI (sparse-clone + render)
DATASET=realkie_charities ./setup_and_run.sh start   # Signal, new domain (5.6 GB download)
DATASET=realkie_nda       ./setup_and_run.sh start   # Signal, new domain (888 MB download)
RUN_ARGS="--resume --max-workers 8 --limit 2000" \
  DATASET=realkie_s1      ./setup_and_run.sh start   # Signal, financial domain (3.9 GB; pages, so --limit)
# (already done earlier: DATASET=fatura / realkie_fcc / realkie_charities / realkie_nda / vrdu)
# NOTE: kill the old tmux session before each new dataset — `tmux kill-session -t ebv_extract`
# (otherwise `start` just re-attaches to the finished session instead of launching the new run).
```
`start` is resumable (`--resume`): if the box restarts, re-run the same line and it
continues. Detach tmux with `Ctrl+B` then `D`; reattach with `tmux attach -t ebv_extract`.
Manual (two terminals) if you prefer no tmux:
```bash
source .venv/bin/activate
bash serve_nuextract.sh &                       # vLLM OpenAI server on :30000
python run_extraction.py --dataset fatura --resume --max-workers 8
python run_extraction.py --dataset realkie_fcc --resume
```

## What gets written (`results/`)
Matches the NER-harness format the NTP/EBV pipeline expects, plus an explicit `doc_type`:
```jsonc
// extraction_results_<dataset>.json
{
  "Template1_Instance0": {
    "NuExtract3": {
      "doc_type": "invoice",
      "extracted": { "BUYER": "…", "DATE": "…", "TOTAL": "1,234.56", "DISCOUNT": null },
      "metrics": { "latency_s": 1.2, "input_tokens": 1500, "output_tokens": 90, "parse_ok": true }
    }
  }
}
```
```jsonc
// ground_truth_<dataset>.json   (for the Stage-2 correct/wrong labelling)
{ "Template1_Instance0": { "BUYER": "…", "DATE": "…", "TOTAL": "1,234.56" } }
```
`batch_summary_<dataset>.json` records counts, elapsed, the field schema, and the run config.

The `extracted` object is a flat `{field: value}` map (string / number / null) — exactly the
shape the NTP verifier consumes. `doc_type` is added so NTP can route (the original NER output
omitted it).

## Datasets (adapters)
- **FATURA** (`--dataset fatura`): single-page synthetic invoices. Default = the **full set**,
  all 50 templates × 200 instances (**10,000 docs**). Narrow it with `--templates 1,12,25,37,49
  --sample-per-template 100` if you want a sample. Input = page image (ROI mode is spatial).
  Field schema is derived from `Annotations/Original_Format`, sampling a few instances of **every**
  template so the field set is complete and stable regardless of how many docs you run.
- **RealKIE-FCC** (`--dataset realkie_fcc`): multi-page real invoices, whole 370-doc subset.
  Input defaults to **text** (cheapest; Signal is text-based) — use `--input-mode image` to feed
  page PNGs instead. Field schema derived from the `labels` column.
- **RealKIE-Charities** (`--dataset realkie_charities`): real UK nonprofit reports, 28 fields,
  ~538 docs. Same adapter/format as FCC (text mode). Different domain → Signal generalization.
- **RealKIE-NDA** (`--dataset realkie_nda`): real non-disclosure agreements, 3 fields, ~439 docs,
  near-linear text. Same adapter/format (text mode). Second new Signal domain.
- **RealKIE-S1** (`--dataset realkie_s1`): SEC IPO registration (S-1) filings, 24 fields. RealKIE
  ships them **pre-split into single pages** (13,079 page segments from 322 filings, ~660 words each),
  so each row is short/clean (no truncation) but there are many rows — cap with `--limit` (e.g.
  `--limit 2000`). Financial Signal domain. Page rows that share a filename get a `__pN` doc-id suffix
  so none overwrite each other. (Resource Contracts — 198 docs, ~85 pages each — is deferred: a 38 GB
  `.7z` and truncation-dominated.)
- **VRDU** (`--dataset vrdu`): **REAL templatic** FARA registration forms (1,915 docs, 3 templates,
  6 fields, per-field boxes) — the real-document counterpart to synthetic FATURA for the ROI verifier.
  Ships PDFs + `dataset.jsonl` (OCR+annotations); `prep_vrdu.py` renders page PNGs for **image** mode.
  `setup_and_run.sh` runs the sparse-clone + prep automatically; to redo it manually:
  `python prep_vrdu.py` (needs `poppler-utils`). GT/field-schema come from the annotations union.

## Config knobs (env or `config.py`)
| var | default | meaning |
|---|---|---|
| `NUEXTRACT_MODEL_ID` | `numind/NuExtract3` | HF repo (use `numind/NuExtract3-W4A16` for 4-bit) |
| `NUEXTRACT_PORT` | `30000` | vLLM server port |
| `NUEXTRACT_TEMPERATURE/_TOP_P/_MAX_TOKENS` | `0.1 / 0.9 / 4096` | generation |
| `FATURA_ROOT`, `REALKIE_FCC_ROOT` | `../fatura`, `../realkie_fcc_invoices` | dataset dirs |
| `EBV_RESULTS_DIR` | `experiments/results` | output dir |

## Notes
- **Serve ≠ GGUF.** NuExtract 3 is Qwen3.5-VL-based → served with `vllm serve` (OpenAI API). The
  `NuExtract3-Q4_K_M.gguf` is the llama.cpp path (no efficient batching) — not used here.
- **A10 fit:** BF16 `numind/NuExtract3` (~10 GB) fits 24 GB with headroom; W4A16 gives more room.
- **Cost:** keep docs short/single-page where possible; FATURA is sampled, RealKIE-FCC defaults to text.
- **Error supply:** NuExtract is a realistic mid-tier extractor, so its natural mistakes are what we
  verify. If FATURA (synthetic/clean) yields too few errors, top up later with a corruption generator.
- `--trust-remote-code` / `--limit-mm-per-prompt` flags in `serve_nuextract.sh` may need tweaking to
  your exact vLLM version (see comments in that file).
