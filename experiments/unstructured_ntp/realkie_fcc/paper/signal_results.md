# Signal (unstructured) NTP — FCC results

| population / mode | n | err-rate | error-catch ↑ | false-alarm ↓ | route-prec ↑ | accuracy ↑ | AUROC ↑ | cov@5% ↑ |
|---|---|---|---|---|---|---|---|---|
| all / binary | 484 | 0.2893 | 0.8929 | 0.5349 | 0.4045 | 0.5888 | 0.7576 | 0.0517 |
| all / 3tier | 484 | 0.2893 | 0.9071 | 0.5901 | 0.3848 | 0.5537 | 0.7576 | 0.0517 |
| scalar / binary | 264 | 0.1932 | 0.8627 | 0.4554 | 0.3121 | 0.6061 | 0.8036 | 0.3864 |
| scalar / 3tier | 264 | 0.1932 | 0.8824 | 0.507 | 0.2941 | 0.5682 | 0.8036 | 0.3864 |

Sufficiency: empty_prior_applied=0, gated=11, 3-tier={'NTP': 154, 'LLM_REVIEW': 97, 'HUMAN_REVIEW': 233}
