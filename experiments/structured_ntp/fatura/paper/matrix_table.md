# Controlled 8-way comparison (structured ROI, FATURA)

↑ = higher is better, ↓ = lower is better. Correctness is a label on the SAME accept/route decisions.

| version | config | correctness | n | err-rate | error-catch ↑ | false-alarm ↓ | route-prec ↑ | accuracy ↑ | AURC ↓ |
|---|---|---|---|---|---|---|---|---|---|
| v1 | pred-ROI, NO calib | exact | 28468 | 0.102 | 0.5348 | 0.0503 | 0.5470 | 0.9074 | 0.0115 |
| v1 | pred-ROI, NO calib | containment | 29199 | 0.056 | 0.9994 | 0.0497 | 0.5425 | 0.9530 | 0.0002 |
| v2 | pred-ROI, calib+layers | exact | 28468 | 0.102 | 0.6119 | 0.0446 | 0.6092 | 0.9204 | 0.0098 |
| v2 | pred-ROI, calib+layers | containment | 29199 | 0.056 | 0.9994 | 0.0388 | 0.6031 | 0.9633 | 0.0002 |
| v3 | GT-ROI, calib+layers (prod) | exact | 28468 | 0.102 | 0.6143 | 0.0870 | 0.4451 | 0.8825 | 0.0093 |
| v3 | GT-ROI, calib+layers (prod) | containment | 29199 | 0.056 | 1.0000 | 0.0963 | 0.3801 | 0.9091 | 0.0000 |
| v4 | GT-ROI, NO calib | exact | 28468 | 0.102 | 0.5954 | 0.0915 | 0.4250 | 0.8766 | 0.0091 |
| v4 | GT-ROI, NO calib | containment | 29199 | 0.056 | 1.0000 | 0.1058 | 0.3580 | 0.9001 | 0.0001 |
