# SST Multi-Topology Panel Report

Overall panel classification: **0_PASS_16_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| fremlin:8_8:knot.8_8d | knot | 1 | FAIL | 0.3447 | -0.070673 | -0.0018 | FAIL | NO |
| knotplot:knot_6.3 | knot | 1 | FAIL | 0.1199 | 0.16138 | 0.0154 | FAIL | NO |
| fremlin:4_1:knot.4_1d | knot | 1 | FAIL | 0.5960 | -0.54449 | -0.0803 | FAIL | NO |
| knotplot:knot_10.123 | knot | 1 | FAIL | 0.3072 | -0.12645 | 0.0001 | FAIL | NO |
| knotplot:knot_9.1 | knot | 1 | FAIL | 0.2980 | 0.33809 | 0.0000 | FAIL | NO |
| knotplot:link_7.2.6 | link | 2 | FAIL | 0.0861 | 2.3821 | -0.0022 | FAIL | NO |
| fremlin:8_2:knot.8_2 | knot | 1 | FAIL | 0.2523 | 0.068279 | 0.0197 | FAIL | NO |
| knotplot:torus_2.8 | torus_link | 2 | FAIL | 0.2615 | 0.1466 | -0.0123 | FAIL | NO |
| fremlin:8_3:knot.8_3z | knot | 1 | FAIL | 0.4453 | 0.21028 | -0.0327 | FAIL | NO |
| fremlin:8_11:knot.8_11d | knot | 1 | FAIL | 0.2497 | 0.41438 | -0.0165 | FAIL | NO |
| fremlin:5_2:knot.5_2r | knot | 1 | FAIL | 0.6460 | 0.37413 | -0.0540 | FAIL | NO |
| fremlin:7_1:knot.7_1p | knot | 1 | FAIL | 0.5345 | -0.13764 | 0.0096 | FAIL | NO |
| knotplot:knot_5.1 | knot | 1 | FAIL | 0.2174 | -0.076086 | -0.0067 | FAIL | NO |
| fremlin:12a_1202:knot.12a_1202 | knot | 1 | FAIL | 0.0692 | -1.5247 | 0.0131 | FAIL | NO |
| fremlin:7_5:knot.7_5d | knot | 1 | FAIL | 0.4358 | 0.30805 | -0.0067 | FAIL | NO |
| fremlin:8_15:knot.8_15d | knot | 1 | FAIL | 1.0000 | 0.60448 | 0.0708 | FAIL | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
