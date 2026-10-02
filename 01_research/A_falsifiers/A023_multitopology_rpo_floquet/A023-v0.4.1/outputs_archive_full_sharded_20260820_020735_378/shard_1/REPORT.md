# SST Multi-Topology Panel Report

Overall panel classification: **1_PASS_15_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| fremlin:8_7:knot.8_7s | knot | 1 | FAIL | 0.2610 | -1.4905e-13 | 0.0146 | FAIL | NO |
| knotplot:link_6.2.1 | link | 2 | FAIL | 0.1941 | -0.073216 | -0.0565 | FAIL | NO |
| fremlin:4_1:knot.4_1 | knot | 1 | FAIL | 0.3264 | 0.34547 | -0.0178 | FAIL | NO |
| knotplot:knot_10.1 | knot | 1 | FAIL | 0.1175 | 0.1555 | 0.0047 | FAIL | NO |
| knotplot:link_8.2.1 | link | 2 | FAIL | 0.0375 | -1.1324 | 0.0053 | FAIL | NO |
| knotplot:link_7.2.5 | link | 2 | FAIL | 0.0635 | 1.1365 | 0.0192 | FAIL | NO |
| fremlin:8_19:knot.8_19u | knot | 1 | FAIL | 0.8792 | 0.20461 | 0.0889 | FAIL | NO |
| knotplot:torus_2.7 | torus_knot | 1 | FAIL | 0.3592 | 0.19745 | -0.1775 | FAIL | NO |
| fremlin:8_3:knot.8_3d | knot | 1 | FAIL | 0.4418 | -1.3501 | -0.0081 | FAIL | NO |
| fremlin:8_11:knot.8_11 | knot | 1 | FAIL | 0.3353 | -0.027057 | 0.0608 | FAIL | NO |
| fremlin:5_2:knot.5_2d | knot | 1 | FAIL | 0.3082 | 0.72328 | -0.0400 | FAIL | NO |
| fremlin:7_1:knot.7_1 | knot | 1 | FAIL | 0.3620 | 0.17492 | -0.1811 | FAIL | NO |
| knotplot:link_4.2.1 | link | 2 | PASS | 0.0909 | 0.60284 | -0.0454 | PASS | NO |
| fremlin:10_1:knot.10_1n | knot | 1 | FAIL | 0.1076 | 0.12879 | -0.0083 | FAIL | NO |
| fremlin:7_5:knot.7_5 | knot | 1 | FAIL | 0.1240 | 2.6901e-13 | 0.0245 | FAIL | NO |
| fremlin:8_15:knot.8_15 | knot | 1 | FAIL | 1.0000 | 0.057897 | -0.0096 | FAIL | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
