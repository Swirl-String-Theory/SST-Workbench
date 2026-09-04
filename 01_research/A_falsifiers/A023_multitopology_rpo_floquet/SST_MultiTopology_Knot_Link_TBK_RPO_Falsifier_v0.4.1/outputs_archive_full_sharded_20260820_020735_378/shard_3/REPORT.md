# SST Multi-Topology Panel Report

Overall panel classification: **0_PASS_16_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| fremlin:8_9:knot.8_9d | knot | 1 | FAIL | 1.0000 | -0.83894 | -0.0176 | FAIL | NO |
| knotplot:link_6.3.1 | link | 3 | FAIL | 0.1141 | 0.52506 | -0.0299 | FAIL | NO |
| fremlin:4_1:knot.4_1p | knot | 1 | FAIL | 0.8627 | 7.2898e-14 | -0.0189 | FAIL | NO |
| knotplot:torus_2.11 | torus_knot | 1 | FAIL | 0.4661 | -0.40989 | 0.0000 | FAIL | NO |
| knotplot:knot_9.2 | knot | 1 | FAIL | 0.1662 | -0.074638 | 0.0169 | FAIL | NO |
| knotplot:link_7.2.8 | link | 2 | FAIL | 0.1905 | -0.44931 | -0.0181 | FAIL | NO |
| fremlin:8_2:knot.8_2d | knot | 1 | FAIL | 1.0000 | 0.38843 | -0.0392 | FAIL | NO |
| knotplot:torus_2.9 | torus_knot | 1 | FAIL | 0.2980 | 0.24458 | 0.0000 | FAIL | NO |
| fremlin:8_4:knot.8_4 | knot | 1 | FAIL | 1.0000 | 1.097e-13 | -0.0278 | FAIL | NO |
| fremlin:8_12:knot.8_12d | knot | 1 | FAIL | 0.1777 | -2.3047 | 0.0011 | FAIL | NO |
| fremlin:6_1:knot.6_1 | knot | 1 | FAIL | 0.1997 | -2.8449e-14 | -0.0203 | FAIL | NO |
| fremlin:7_2:knot.7_2 | knot | 1 | FAIL | 0.0863 | 0.073011 | 0.0046 | FAIL | NO |
| knotplot:knot_5.2 | knot | 1 | FAIL | 0.0413 | 0.2467 | 0.0083 | FAIL | NO |
| fremlin:12a_1202:knot.12a_1202z6 | knot | 1 | FAIL | 0.3420 | -0.12625 | 0.0033 | FAIL | NO |
| fremlin:7_6:knot.7_6d | knot | 1 | FAIL | 0.5364 | 0.94635 | -0.0321 | FAIL | NO |
| fremlin:8_15:knot.8_15p | knot | 1 | FAIL | 0.5789 | 1.1143e-12 | -0.0290 | FAIL | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
