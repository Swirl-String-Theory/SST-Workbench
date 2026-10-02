# SST Multi-Topology Panel Report

Overall panel classification: **0_PASS_16_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| fremlin:9_2:knot.9_2n | knot | 1 | FAIL | 0.1207 | 0.80198 | -0.0201 | FAIL | NO |
| knotplot:link_6.3.3 | link | 3 | FAIL | 0.0649 | 0.44651 | -0.0016 | FAIL | NO |
| fremlin:5_1:knot.5_1 | knot | 1 | FAIL | 0.3543 | 0.38137 | 0.0000 | FAIL | NO |
| knotplot:torus_2.3 | torus_knot | 1 | FAIL | 0.1791 | -0.039963 | -0.0354 | PASS | NO |
| knotplot:link_9.2.40 | link | 2 | FAIL | 0.0571 | -1.169 | 0.0040 | FAIL | NO |
| knotplot:knot_7.4 | knot | 1 | FAIL | 0.0520 | 0.12226 | 0.0061 | FAIL | NO |
| fremlin:8_21:knot.8_21d | knot | 1 | FAIL | 1.0000 | -0.30669 | -0.0194 | FAIL | NO |
| knotplot:torus_3.3 | torus_link | 3 | FAIL | 0.1194 | -0.24524 | -0.0121 | FAIL | NO |
| fremlin:8_5:knot.8_5 | knot | 1 | FAIL | 0.4295 | -0.0037146 | 0.0052 | FAIL | NO |
| fremlin:8_13:knot.8_13d | knot | 1 | FAIL | 1.0000 | -0.46693 | -0.0127 | FAIL | NO |
| fremlin:6_2:knot.6_2d | knot | 1 | FAIL | 0.3343 | -0.056649 | -0.0116 | FAIL | NO |
| fremlin:7_2:knot.7_2r | knot | 1 | FAIL | 0.5513 | -7.3294e-14 | -0.0859 | FAIL | NO |
| knotplot:knot_6.1 | knot | 1 | FAIL | 0.1118 | 0.084244 | -0.0196 | FAIL | NO |
| fremlin:1_1:knot.1_1 | unknot | 1 | FAIL | 0.3199 | 0 | -0.0000 | PASS | NO |
| fremlin:7_7:knot.7_7d | knot | 1 | FAIL | 0.8515 | -0.16346 | -0.0147 | FAIL | NO |
| fremlin:8_17:knot.8_17 | knot | 1 | FAIL | 0.3089 | 0.361 | 0.0237 | FAIL | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
