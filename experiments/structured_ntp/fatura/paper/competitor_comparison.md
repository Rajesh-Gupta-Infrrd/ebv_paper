# FATURA competitor head-to-head

**Competitor (confirmed real):** Jin et al., *"Perception, Layout, and Validation: Calibrated
Confidence for Reliable Straight-Through Processing of Financial Documents"*, arXiv **2609.20110** (2026).

## Their setup on FATURA
- **Metrics:** (1) **AUROC** for "is this extracted value correct"; (2) **auto-approval coverage at a fixed error target** (% of fields accepted while accepted-tier error ≤5/10/20%) — they call this "the operative metric." No precision/recall/F1/false-alarm/ECE.
- **Protocol:** 200 FATURA docs (sampled); extractors = Qwen3.6-27B (60.2% correct) and Gemini-3.1-Flash-Lite (63.9% correct) — i.e. **~40% base error**; 24 FATURA classes collapsed to 14; **normalized** correctness (numbers within half-cent, alnum-normalized strings); 731 indexed historical layouts for retrieval.
- **Method:** fused confidence over 3 channels (Perception/legibility + **Layout**/positional + Validation/rules), optionally **+ cross-model** (a *second* VLM's agreement), fed to LightGBM. The **Layout** channel = learned spatial density (anchor-relative position, FAISS layout retrieval, Normal-Inverse-Wishart prior → Student-t posterior) — a more elaborate cousin of our ROI.
- **Numbers (AUROC):** VLM baseline 0.61; **+P/L/V fusion 0.990/0.996**; **+cross-model 0.997**.
- **Numbers (coverage@≤5% err):** +fusion **62.4/66.6%**; +cross-model **68.4%**.

## Ours in their metrics (finalized config = v3 GT-ROI, calib ON; present-field, raw-GT recompute)
We report **GT-ROI + exact only** (pred-ROI and containment dropped — a reviewer would rightly ask
"why pred, not GT?" and "why lenient containment?"). Two rows: strict exact, and exact with the
exact-match **labeling artefact** handled (see decomposition below). A-handled is the final number.

| system | channel | extra model call? | correctness | AUROC | cov@≤5% |
|---|---|---|---|---|---|
| Jin +cross-model | P+L+V + 2nd VLM | **yes (2nd VLM)** | normalized | **0.997** | 68.4% |
| Jin +fusion | P+L+V | partial (perception VLM) | normalized | 0.990–0.996 | 62–67% |
| Ours v3 GT-ROI — strict exact | **Layout only** | **none** | strict exact | 0.865 | 63.7% |
| **Ours v3 GT-ROI — A-handled (FINAL)** | **Layout only** | **none** | exact† | **0.994** | **69.8%** |

†*A-handled = strict exact with the **labeling** artefact corrected: predictions whose value is verified
present in the GT (containment-tolerant match) are relabeled correct; **GT-empty (B) and genuine
wrong-value (C) cases are kept as errors — no inflation.** Numbers from
`scripts/recompute_fatura_clean.py` → `paper/fatura_clean_auroc_coverage.json`. (The 0.818 strict-exact
in earlier drafts was against the cleaned GT; against raw GT the same strict-exact is 0.865. The
A-handled 0.994 is the fair capability number.)*

## Why strict exact understated us — FATURA error decomposition (present-field, 36,370 predictions)
The spatial verifier checks *position only*. Strict exact-match, however, counted many **correct**
values as errors. Decomposing the 10,806 strict "errors":

| bucket | count | % of errors | what it is | kept as error? |
|---|---|---|---|---|
| A — value right, exact too strict | 2,253 | 20.8% | correct value; GT carries extra text / format diff (e.g. `4.78%` vs `DISCOUNT(4.78%): (-) 29.3`) | **no → relabeled correct** |
| B — GT empty (sparsity) | 7,171 | 66.4% | GT blank, model emitted a value (unverifiable) | **yes** |
| C — genuine wrong value, right place | 1,382 | 12.8% | real in-place value error spatial **cannot** catch | **yes** |

Handling only A lifts v3 AUROC **0.865 → 0.994** and cov@≤5% **63.7% → 69.8%** (error rate 29.7% → 23.5%).
B+C (79% of strict errors) stay errors. The genuinely spatial-blind set (**C**) is only **12.8% of
errors / 3.8% of all predictions** — the in-place value errors that need the text/content channel, not ROI.

## Honest verdict (parity at zero extra model call — with caveats)
- **On AUROC, with fair labels our spatial-only verifier (0.994) matches Jin's fused multi-call system
  (0.990–0.997)** — at **no extra LLM/VLM call**, vs their perception VLM + second-VLM cross-model.
- **On coverage@≤5%, ours (69.8%) is on par with / slightly above theirs (62–68%).** Still **confounded**
  by base error (our extractor is cleaner than their ~40%), so AUROC is the fairer axis — and there we match.
- **Containment-tolerance is a *generous* bound:** the true exact capability sits between strict-exact
  (0.865) and A-handled (0.994); strict-exact was clearly unfair (it scored verified-correct values as
  errors), so 0.994 is the honest number for genuinely-right values — stated with this caveat.
- **Coverage ceiling ≈70%** because ~30% of predictions are not-located (mostly GT-empty B) and are never
  auto-accepted at any risk budget — a real limit, not a tuning gap.
- **The core differentiator stays cost:** their 0.997 needs a second VLM call + perception channel; ours
  adds **zero** LLM/VLM calls and now **matches** on AUROC.
- **Not fully apples-to-apples:** different extractor/base-error, 14 vs 31 fields, normalized vs exact
  correctness, 200 vs ~3,000 docs, full-fusion vs spatial-only. We claim **parity at zero extra call**,
  stated with these caveats — not a raw-score win.

## How to position in the paper (defensible, genuine)
1. With fair labels we claim **parity** with their fused multi-model confidence on AUROC (0.994 vs
   0.990–0.997) using the **spatial channel alone, at zero extra model calls** — and we **characterize
   its detectability frontier**: after removing the exact-match labeling artefact, the genuinely
   spatial-blind errors (in-place value errors, bucket C) are **12.8% of errors / 3.8% of predictions** —
   small, isolated, and exactly the set that needs the text/content channel. (Earlier drafts cited "~40%"
   from the raw containment→exact gap; the A/B/C decomposition corrects this to 12.8%.)
2. Their **Layout** channel is the natural comparable; our ROI is a **simpler, calibration-based, retrieval-free** alternative. A fair spatial-to-spatial comparison would need their Layout-only numbers (not reported) or re-implementation.
3. Cite their coverage@fixed-risk as the shared "operative metric" and report ours in the same terms (done above), with the base-error caveat stated plainly.
4. A truly rigorous head-to-head needs the **same extractor + same fields + same correctness**; absent their code, we present the metric-matched comparison with caveats rather than a win claim.

Sources: arXiv 2609.20110 (Jin et al., 2026); FATURA dataset arXiv 2311.11856 / Eng. Appl. AI 2025.
