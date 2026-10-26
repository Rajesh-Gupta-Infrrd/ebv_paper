| config | population | catch ↑ | false-alarm ↓ | accuracy ↑ | AUROC ↑ | cov@5% ↑ |
|---|---|---|---|---|---|---|
| untuned (--skip-tuning) | scalar | 0.863 | 0.455 | 0.606 | 0.8036 | 0.386 |
| untuned (--skip-tuning) | all | 0.893 | 0.535 | 0.589 | 0.7576 | 0.052 |
| tuned (RandomizedSearchCV) | scalar | 0.961 | 0.662 | 0.458 | 0.8126 | 0.409 |
| tuned (RandomizedSearchCV) | all | 0.907 | 0.666 | 0.5 | 0.7509 | 0.002 |
