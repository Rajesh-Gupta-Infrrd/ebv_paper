# Signal (unstructured) NTP — realkie_nda robustness results

doc_type = `nda`. Same dociq Signal classifier + 6 text signals as the FCC leg (no extra model call), driven in place; dociq untouched. Built with the GT-sparsity cleanup (`clean`, canonical) and the pre-fix labels (`noisy`) + a tuned (RandomizedSearchCV) variant.

> This domain has **no line-item/tabular fields** → `scalar` == `all` population.

## TL;DR (canonical = clean · untuned · binary · scalar)
- AUROC **0.5316**, accuracy 0.5405 (accept-all 0.9122), error-catch 0.4615, cov@5% 0.1622 (n=148, err=0.0878).
- Quote the **AUROC/coverage** (capability), not accuracy (see the FCC doc §6 for why).

## 1. Canonical (clean) — all populations/modes
| run · pop · mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clean · scalar · binary | 148 | 0.0878 | 0.4615 | 0.4519 | 0.0896 | 0.5405 | 0.9122 | 0.5316 | 0.1622 | 1.0000 | 1.0000 |
| clean · scalar · 3tier | 148 | 0.0878 | 0.4615 | 0.5333 | 0.0769 | 0.4662 | 0.9122 | 0.5316 | 0.1622 | 1.0000 | 1.0000 |
| clean · all · binary | 148 | 0.0878 | 0.4615 | 0.4519 | 0.0896 | 0.5405 | 0.9122 | 0.5316 | 0.1622 | 1.0000 | 1.0000 |
| clean · all · 3tier | 148 | 0.0878 | 0.4615 | 0.5333 | 0.0769 | 0.4662 | 0.9122 | 0.5316 | 0.1622 | 1.0000 | 1.0000 |

## 2. Tuning: untuned(noisy) vs tuned(noisy)
| run · pop · mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| noisy · scalar · binary | 150 | 0.1 | 0.4000 | 0.2370 | 0.1579 | 0.7267 | 0.9000 | 0.5620 | 0.1600 | 1.0000 | 1.0000 |
| noisy · scalar · 3tier | 150 | 0.1 | 0.4667 | 0.4222 | 0.1094 | 0.5667 | 0.9000 | 0.5620 | 0.1600 | 1.0000 | 1.0000 |
| noisy · all · binary | 150 | 0.1 | 0.4000 | 0.2370 | 0.1579 | 0.7267 | 0.9000 | 0.5620 | 0.1600 | 1.0000 | 1.0000 |
| noisy · all · 3tier | 150 | 0.1 | 0.4667 | 0.4222 | 0.1094 | 0.5667 | 0.9000 | 0.5620 | 0.1600 | 1.0000 | 1.0000 |
| tuned · scalar · binary | 150 | 0.1 | 0.3333 | 0.1852 | 0.1667 | 0.7667 | 0.9000 | 0.5995 | 0.1533 | 1.0000 | 1.0000 |
| tuned · scalar · 3tier | 150 | 0.1 | 0.4667 | 0.4000 | 0.1148 | 0.5867 | 0.9000 | 0.5995 | 0.1533 | 1.0000 | 1.0000 |
| tuned · all · binary | 150 | 0.1 | 0.3333 | 0.1852 | 0.1667 | 0.7667 | 0.9000 | 0.5995 | 0.1533 | 1.0000 | 1.0000 |
| tuned · all · 3tier | 150 | 0.1 | 0.4667 | 0.4000 | 0.1148 | 0.5867 | 0.9000 | 0.5995 | 0.1533 | 1.0000 | 1.0000 |

_Tuning = RandomizedSearchCV only (same data/signals/algorithm)._

## 3. Before vs after the GT-sparsity cleanup (noisy → clean, untuned)
| run · pop · mode | n | err | catch ↑ | FA ↓ | route-prec ↑ | acc | accept-all acc | AUROC ↑ | cov@5% | cov@10% | cov@20% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| noisy · scalar · binary | 150 | 0.1 | 0.4000 | 0.2370 | 0.1579 | 0.7267 | 0.9000 | 0.5620 | 0.1600 | 1.0000 | 1.0000 |
| noisy · scalar · 3tier | 150 | 0.1 | 0.4667 | 0.4222 | 0.1094 | 0.5667 | 0.9000 | 0.5620 | 0.1600 | 1.0000 | 1.0000 |
| noisy · all · binary | 150 | 0.1 | 0.4000 | 0.2370 | 0.1579 | 0.7267 | 0.9000 | 0.5620 | 0.1600 | 1.0000 | 1.0000 |
| noisy · all · 3tier | 150 | 0.1 | 0.4667 | 0.4222 | 0.1094 | 0.5667 | 0.9000 | 0.5620 | 0.1600 | 1.0000 | 1.0000 |
| clean · scalar · binary | 148 | 0.0878 | 0.4615 | 0.4519 | 0.0896 | 0.5405 | 0.9122 | 0.5316 | 0.1622 | 1.0000 | 1.0000 |
| clean · scalar · 3tier | 148 | 0.0878 | 0.4615 | 0.5333 | 0.0769 | 0.4662 | 0.9122 | 0.5316 | 0.1622 | 1.0000 | 1.0000 |
| clean · all · binary | 148 | 0.0878 | 0.4615 | 0.4519 | 0.0896 | 0.5405 | 0.9122 | 0.5316 | 0.1622 | 1.0000 | 1.0000 |
| clean · all · 3tier | 148 | 0.0878 | 0.4615 | 0.5333 | 0.0769 | 0.4662 | 0.9122 | 0.5316 | 0.1622 | 1.0000 | 1.0000 |

## 4. Per-signal separation (clean; mean signal value, correct vs wrong)
| signal | mean(correct) | mean(wrong) |
|---|---|---|
| format_valid | 0.7700 | 0.8230 |
| keyword_context | 0.3640 | 0.3040 |
| source_context | 0.6260 | 0.4620 |
| value_in_text | 0.9000 | 0.5000 |
| label_value_distance | 0.5080 | 0.3920 |
| partial_extraction | 0.5000 | — |

Sufficiency (clean): empty_prior_applied=0, gated=0, 3-tier={'NTP': 70, 'LLM_REVIEW': 31, 'HUMAN_REVIEW': 47}

## 5. Data & split
- clean: 248 docs (198 train / 50 test), 732 field instances (scalar 732, lineitem 0), dropped_unlabelled=12, skipped=0.
- Provenance: predictions+GT `experiments/results/realkie_nda_results/`, text `realkie_nda/train.csv`. Decisions: `domains/realkie_nda/decisions/`.

