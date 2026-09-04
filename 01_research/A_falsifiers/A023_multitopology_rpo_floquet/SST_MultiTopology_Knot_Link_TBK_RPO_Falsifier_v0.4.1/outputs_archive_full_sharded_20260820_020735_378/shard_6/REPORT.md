# SST Multi-Topology Panel Report

Overall panel classification: **0_PASS_16_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| knotplot:knot_0.1 | unknot | 1 | FAIL | 0.3195 | 0 | -0.0146 | PASS | NO |
| knotplot:torus_6.9 | torus_link | 3 | FAIL | 0.3850 | 1.4822 | 0.0075 | FAIL | NO |
| fremlin:5_1:knot.5_1p | knot | 1 | FAIL | 0.3504 | -0.23868 | -0.0824 | FAIL | NO |
| knotplot:torus_2.4 | torus_link | 2 | FAIL | 0.1631 | -0.2122 | -0.0105 | FAIL | NO |
| knotplot:knot_9.35 | knot | 1 | FAIL | 0.0900 | -0.20315 | -0.0218 | FAIL | NO |
| knotplot:knot_8.1 | knot | 1 | FAIL | 0.1430 | 0.21807 | 0.0028 | FAIL | NO |
| fremlin:8_21:knot.8_21p | knot | 1 | FAIL | 0.8725 | 2.348e-12 | 0.0189 | FAIL | NO |
| knotplot:torus_3.6 | torus_link | 3 | FAIL | 0.4289 | 0.7076 | 0.0243 | FAIL | NO |
| fremlin:8_6:knot.8_6 | knot | 1 | FAIL | 0.2162 | 3.854e-13 | -0.0615 | FAIL | NO |
| fremlin:8_13:knot.8_13p | knot | 1 | FAIL | 0.9767 | 5.2792e-13 | -0.0005 | FAIL | NO |
| fremlin:6_2:knot.6_2p | knot | 1 | FAIL | 0.4159 | 1.4109e-13 | 0.0298 | FAIL | NO |
| fremlin:7_3:knot.7_3 | knot | 1 | FAIL | 0.2352 | -8.09e-14 | -0.0209 | FAIL | NO |
| knotplot:torus_6.15 | torus_link | 3 | FAIL | 0.5235 | -1.3053 | -0.0202 | FAIL | NO |
| fremlin:3_1:knot.3_1 | knot | 1 | FAIL | 0.2574 | -0.24953 | -0.0399 | PASS | NO |
| fremlin:8_1:knot.8_1 | knot | 1 | FAIL | 0.4713 | -6.1493e-14 | -0.0453 | FAIL | NO |
| fremlin:8_18:knot.8_18 | knot | 1 | FAIL | 0.4938 | -0.113 | -0.0515 | FAIL | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
