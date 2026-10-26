# Signal (unstructured) NTP — realkie_charities robustness results

doc_type = `charity_report`. Same dociq Signal classifier + 6 text signals as the FCC leg (no extra model call), driven in place; dociq untouched. Built with the GT-sparsity cleanup (`clean`, canonical) and the pre-fix labels (`noisy`) + a tuned (RandomizedSearchCV) variant.

> This domain has **no line-item/tabular fields** → `scalar` == `all` population.

## TL;DR (canonical = clean · untuned · binary · scalar)
- AUROC **0.7129**, accuracy 0.6413 (accept-all 0.9297), error-catch 0.7290, cov@5% 0.7510 (n=1522, err=0.0703).
- Quote the **AUROC/coverage** (capability), not accuracy (see the FCC doc §6 for why).

## 1. Canonical (clean) — all populations/modes
| run · pop · mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clean · scalar · binary | 1522 | 0.0703 | 0.7290 | 0.3654 | 0.1311 | 0.6413 | 0.9297 | 0.7129 | 0.7510 | 1.0000 | 1.0000 |
| clean · scalar · 3tier | 1522 | 0.0703 | 0.7664 | 0.3880 | 0.1300 | 0.6229 | 0.9297 | 0.7129 | 0.7510 | 1.0000 | 1.0000 |
| clean · all · binary | 1522 | 0.0703 | 0.7290 | 0.3654 | 0.1311 | 0.6413 | 0.9297 | 0.7129 | 0.7510 | 1.0000 | 1.0000 |
| clean · all · 3tier | 1522 | 0.0703 | 0.7664 | 0.3880 | 0.1300 | 0.6229 | 0.9297 | 0.7129 | 0.7510 | 1.0000 | 1.0000 |

## 2. Tuning: untuned(noisy) vs tuned(noisy)
| run · pop · mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| noisy · scalar · binary | 1792 | 0.2104 | 0.8382 | 0.2784 | 0.4451 | 0.7461 | 0.7896 | 0.8289 | 0.5296 | 0.7316 | 0.9732 |
| noisy · scalar · 3tier | 1792 | 0.2104 | 0.8753 | 0.3498 | 0.4000 | 0.6975 | 0.7896 | 0.8289 | 0.5296 | 0.7316 | 0.9732 |
| noisy · all · binary | 1792 | 0.2104 | 0.8382 | 0.2784 | 0.4451 | 0.7461 | 0.7896 | 0.8289 | 0.5296 | 0.7316 | 0.9732 |
| noisy · all · 3tier | 1792 | 0.2104 | 0.8753 | 0.3498 | 0.4000 | 0.6975 | 0.7896 | 0.8289 | 0.5296 | 0.7316 | 0.9732 |
| tuned · scalar · binary | 1792 | 0.2104 | 0.7745 | 0.2466 | 0.4555 | 0.7578 | 0.7896 | 0.8144 | 0.5190 | 0.6842 | 0.9526 |
| tuned · scalar · 3tier | 1792 | 0.2104 | 0.8806 | 0.3845 | 0.3790 | 0.6713 | 0.7896 | 0.8144 | 0.5190 | 0.6842 | 0.9526 |
| tuned · all · binary | 1792 | 0.2104 | 0.7745 | 0.2466 | 0.4555 | 0.7578 | 0.7896 | 0.8144 | 0.5190 | 0.6842 | 0.9526 |
| tuned · all · 3tier | 1792 | 0.2104 | 0.8806 | 0.3845 | 0.3790 | 0.6713 | 0.7896 | 0.8144 | 0.5190 | 0.6842 | 0.9526 |

_Tuning = RandomizedSearchCV only (same data/signals/algorithm)._

## 3. Before vs after the GT-sparsity cleanup (noisy → clean, untuned)
| run · pop · mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| noisy · scalar · binary | 1792 | 0.2104 | 0.8382 | 0.2784 | 0.4451 | 0.7461 | 0.7896 | 0.8289 | 0.5296 | 0.7316 | 0.9732 |
| noisy · scalar · 3tier | 1792 | 0.2104 | 0.8753 | 0.3498 | 0.4000 | 0.6975 | 0.7896 | 0.8289 | 0.5296 | 0.7316 | 0.9732 |
| noisy · all · binary | 1792 | 0.2104 | 0.8382 | 0.2784 | 0.4451 | 0.7461 | 0.7896 | 0.8289 | 0.5296 | 0.7316 | 0.9732 |
| noisy · all · 3tier | 1792 | 0.2104 | 0.8753 | 0.3498 | 0.4000 | 0.6975 | 0.7896 | 0.8289 | 0.5296 | 0.7316 | 0.9732 |
| clean · scalar · binary | 1522 | 0.0703 | 0.7290 | 0.3654 | 0.1311 | 0.6413 | 0.9297 | 0.7129 | 0.7510 | 1.0000 | 1.0000 |
| clean · scalar · 3tier | 1522 | 0.0703 | 0.7664 | 0.3880 | 0.1300 | 0.6229 | 0.9297 | 0.7129 | 0.7510 | 1.0000 | 1.0000 |
| clean · all · binary | 1522 | 0.0703 | 0.7290 | 0.3654 | 0.1311 | 0.6413 | 0.9297 | 0.7129 | 0.7510 | 1.0000 | 1.0000 |
| clean · all · 3tier | 1522 | 0.0703 | 0.7664 | 0.3880 | 0.1300 | 0.6229 | 0.9297 | 0.7129 | 0.7510 | 1.0000 | 1.0000 |

## 4. Per-signal separation (clean; mean signal value, correct vs wrong)
| signal | mean(correct) | mean(wrong) |
|---|---|---|
| format_valid | 0.7430 | 0.7770 |
| keyword_context | 0.4560 | 0.4560 |
| source_context | 0.6170 | 0.6090 |
| value_in_text | 0.9470 | 0.8950 |
| label_value_distance | 0.6310 | 0.5230 |
| partial_extraction | 0.5000 | 0.5000 |

Sufficiency (clean): empty_prior_applied=0, gated=0, 3-tier={'NTP': 891, 'LLM_REVIEW': 110, 'HUMAN_REVIEW': 521}

## 5. Data & split
- clean: 322 docs (258 train / 64 test), 7788 field instances (scalar 7788, lineitem 0), dropped_unlabelled=1228, skipped=0.
- Provenance: predictions+GT `experiments/results/realkie_charities_results/`, text `realkie_charities/train.csv`. Decisions: `domains/realkie_charities/decisions/`.

