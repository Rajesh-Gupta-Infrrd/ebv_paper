# ROCKET GPU run — MinerU (tables) + NuExtract (fields) on the A10

Run the two **GPU-bound extractors** on the A10 to produce *predictions* over the full
ROCKET set (876 docs, all 5 types). Everything else — OCR (already pulled from the DB),
ground truth (`correctedValue`), layout/refinement, Table-Trust + ROI + Signal verification
— runs **locally**. The A10 only does model inference.

> Unified-system goal: both modes run over the **same** ROCKET document pool, so we can say
> we evaluated the one system end-to-end on the full set (no subset jugaad).

---

## 1. Copy to the A10 (run locally)
Bundle the scripts + the PDFs + the per-type field lists (the OCR/GT stay local). Saved to
`~/rocket_transfer/` (stable, easy to scp from — and the returned predictions land there too):
```bash
mkdir -p ~/rocket_transfer
cd ~/Git_Clones/research_papers/ebv_paper/experiments
COPYFILE_DISABLE=1 tar czf ~/rocket_transfer/rocket_a10.tgz --exclude='__pycache__' --exclude='._*' --exclude='*/mineru-venv' --exclude='*/nuextract-venv' \
  extraction/config.py extraction/extractor.py extraction/serve_nuextract.sh \
  rocket_gpu \
  datasets/rocket/*/*.pdf datasets/rocket/*/field_list.json
# ~1.1 GB (the PDFs). Then:
scp ~/rocket_transfer/rocket_a10.tgz <user>@<a10-host>:~/
```
On the A10, unpack so `extraction/`, `rocket_gpu/`, `datasets/` are siblings:
```bash
mkdir -p ~/ebv_experiments && tar xzf ~/rocket_a10.tgz -C ~/ebv_experiments
cd ~/ebv_experiments/rocket_gpu
```

## 2–4. Run it (single orchestrator — `run_rocket.sh`)
One command creates the venvs, serves vLLM in tmux, health-waits, runs, and stops the server.
```bash
cd ~/ebv_experiments/rocket_gpu
./run_rocket.sh install     # create both venvs + deps (idempotent; run once)
./run_rocket.sh smoke       # tiny end-to-end check: URLA x20 fields + CD x20 tables
./run_rocket.sh all         # full run: NuExtract (fields) then MinerU (tables), sequentially
```
Or step by step / with args:
```bash
./run_rocket.sh nuextract                       # fields, full set
./run_rocket.sh nuextract --types URLA --limit 20
./run_rocket.sh mineru                           # tables, full set (single batched vLLM run)
MINERU_BACKEND=pipeline ./run_rocket.sh mineru   # non-vLLM fallback
```
What it does for **NuExtract**: starts `serve_nuextract.sh` (vLLM, :30000) in tmux session
`ebv_nuextract`, polls `/health` until ready (logs to `serve.log`), runs the extractor with the
venv's python (so `fitz`/`requests`/`vllm` resolve), then kills the serve session to free the GPU.
For **MinerU**: one batched `vlm-vllm-engine` run over all PDFs (engine loads once).

Outputs:
- `datasets/rocket/<type>/nuextract/<requestId>.json` — `{extracted: {field: value}, metrics}`
- `datasets/rocket/<type>/mineru/<requestId>.json` — `{tables: [{page_idx, table_html}]}`

tmux tips: `tmux attach -t ebv_nuextract` to watch the server; `tmux kill-session -t ebv_nuextract` to stop it.
For even higher table throughput, parse's `vllm-async-engine` MinerU server (micro-batch) is an
option — ask and I'll wire that variant. (`setup_rocket_gpu.sh` still exists as a setup-only helper;
`run_rocket.sh install` supersedes it.)

## 5. Pull predictions back (run on the A10, then scp)
```bash
cd ~/ebv_experiments/datasets/rocket
tar czf /tmp/rocket_preds.tgz */nuextract */mineru
scp /tmp/rocket_preds.tgz <you>@<local>:/tmp/
```
Locally, drop them next to the rest:
```bash
tar xzf /tmp/rocket_preds.tgz -C ~/Git_Clones/research_papers/ebv_paper/experiments/datasets/rocket
```

## 6. Then (local, no GPU)
- **Fields:** join NuExtract `extracted` (prediction) with DB `correctedValue` (GT) + OCR tokens →
  ROI verifier (URLA/CD, locate via OCR tokens) + Signal verifier (AUS_DU/Bank/CreditReport).
- **Tables:** `table_html` + page image (render from PDF) + docTR witness → Table-Trust score vs vision GT.

## Notes
- **GPU is shared** — run NuExtract and MinerU sequentially, not together.
- **Smoke-test first:** `--limit 20` on one type for each, confirm outputs look right, then run the full set.
- Favor whichever extractor gives the better/cleaner result per mode — both are produced, so we can choose per the paper.
- The A10 only needs the PDFs + field lists; OCR and GT never leave the local box.
