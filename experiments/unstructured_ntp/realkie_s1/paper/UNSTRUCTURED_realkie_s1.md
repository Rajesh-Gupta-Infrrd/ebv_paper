# Signal (unstructured) NTP — realkie_s1 robustness results

doc_type = `s1_filing`. Same dociq Signal classifier + 6 text signals as the FCC leg (no extra model call), driven in place; dociq untouched. Built with the GT-sparsity cleanup (`clean`, canonical) and the pre-fix labels (`noisy`) + a tuned (RandomizedSearchCV) variant.

> This domain has **no line-item/tabular fields** → `scalar` == `all` population.

## TL;DR (canonical = clean · untuned · binary · scalar)
- AUROC **0.9601**, accuracy 0.9620 (accept-all 0.9678), error-catch 0.8383, cov@5% 1.0000 (n=37277, err=0.0322).
- Quote the **AUROC/coverage** (capability), not accuracy (see the FCC doc §6 for why).

## 1. Canonical (clean) — all populations/modes
| run · pop · mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clean · scalar · binary | 37277 | 0.0322 | 0.8383 | 0.0339 | 0.4515 | 0.9620 | 0.9678 | 0.9601 | 1.0000 | 1.0000 | 1.0000 |
| clean · scalar · 3tier | 37277 | 0.0322 | 0.8425 | 0.0354 | 0.4417 | 0.9606 | 0.9678 | 0.9601 | 1.0000 | 1.0000 | 1.0000 |
| clean · all · binary | 37277 | 0.0322 | 0.8383 | 0.0339 | 0.4515 | 0.9620 | 0.9678 | 0.9601 | 1.0000 | 1.0000 | 1.0000 |
| clean · all · 3tier | 37277 | 0.0322 | 0.8425 | 0.0354 | 0.4417 | 0.9606 | 0.9678 | 0.9601 | 1.0000 | 1.0000 | 1.0000 |

## 2. Tuning: untuned(noisy) vs tuned(noisy)
| run · pop · mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| noisy · scalar · binary | 37920 | 0.0486 | 0.8964 | 0.0352 | 0.5652 | 0.9614 | 0.9514 | 0.9645 | 1.0000 | 1.0000 | 1.0000 |
| noisy · scalar · 3tier | 37920 | 0.0486 | 0.8974 | 0.0371 | 0.5526 | 0.9597 | 0.9514 | 0.9645 | 1.0000 | 1.0000 | 1.0000 |
| noisy · all · binary | 37920 | 0.0486 | 0.8964 | 0.0352 | 0.5652 | 0.9614 | 0.9514 | 0.9645 | 1.0000 | 1.0000 | 1.0000 |
| noisy · all · 3tier | 37920 | 0.0486 | 0.8974 | 0.0371 | 0.5526 | 0.9597 | 0.9514 | 0.9645 | 1.0000 | 1.0000 | 1.0000 |

_Tuning = RandomizedSearchCV only (same data/signals/algorithm)._

## 3. Before vs after the GT-sparsity cleanup (noisy → clean, untuned)
| run · pop · mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| noisy · scalar · binary | 37920 | 0.0486 | 0.8964 | 0.0352 | 0.5652 | 0.9614 | 0.9514 | 0.9645 | 1.0000 | 1.0000 | 1.0000 |
| noisy · scalar · 3tier | 37920 | 0.0486 | 0.8974 | 0.0371 | 0.5526 | 0.9597 | 0.9514 | 0.9645 | 1.0000 | 1.0000 | 1.0000 |
| noisy · all · binary | 37920 | 0.0486 | 0.8964 | 0.0352 | 0.5652 | 0.9614 | 0.9514 | 0.9645 | 1.0000 | 1.0000 | 1.0000 |
| noisy · all · 3tier | 37920 | 0.0486 | 0.8974 | 0.0371 | 0.5526 | 0.9597 | 0.9514 | 0.9645 | 1.0000 | 1.0000 | 1.0000 |
| clean · scalar · binary | 37277 | 0.0322 | 0.8383 | 0.0339 | 0.4515 | 0.9620 | 0.9678 | 0.9601 | 1.0000 | 1.0000 | 1.0000 |
| clean · scalar · 3tier | 37277 | 0.0322 | 0.8425 | 0.0354 | 0.4417 | 0.9606 | 0.9678 | 0.9601 | 1.0000 | 1.0000 | 1.0000 |
| clean · all · binary | 37277 | 0.0322 | 0.8383 | 0.0339 | 0.4515 | 0.9620 | 0.9678 | 0.9601 | 1.0000 | 1.0000 | 1.0000 |
| clean · all · 3tier | 37277 | 0.0322 | 0.8425 | 0.0354 | 0.4417 | 0.9606 | 0.9678 | 0.9601 | 1.0000 | 1.0000 | 1.0000 |

## 4. Per-signal separation (clean; mean signal value, correct vs wrong)
| signal | mean(correct) | mean(wrong) |
|---|---|---|
| format_valid | 0.7980 | 0.7950 |
| keyword_context | 0.2640 | 0.3040 |
| source_context | 0.4990 | 0.4740 |
| value_in_text | 0.4330 | 0.2490 |
| label_value_distance | 0.5000 | 0.4880 |
| partial_extraction | — | — |

Sufficiency (clean): empty_prior_applied=3083, gated=3034, 3-tier={'NTP': 34988, 'LLM_REVIEW': 131, 'HUMAN_REVIEW': 2158}

## 5. Data & split
- clean: 7901 docs (6321 train / 1580 test), 186069 field instances (scalar 186069, lineitem 0), dropped_unlabelled=3555, skipped=0.
- Provenance: predictions+GT `experiments/results/realkie_s1_results/`, text `realkie_s1/train.csv`. Decisions: `domains/realkie_s1/decisions/`.

