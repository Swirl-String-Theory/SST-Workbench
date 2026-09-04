# SST Multi-Topology Panel Report

Overall panel classification: **0_PASS_15_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| knotplot:link_0.2.1 | unlink | 2 | FAIL | 0.2419 | 4.6244e-13 | 0.0000 | PASS | NO |
| knotplot:knot_6.2 | knot | 1 | FAIL | 0.1192 | 0.23328 | -0.0239 | FAIL | NO |
| fremlin:5_1:knot.5_1u | knot | 1 | FAIL | 1.0000 | -0.028989 | 0.0357 | FAIL | NO |
| knotplot:torus_2.5 | torus_knot | 1 | FAIL | 0.2803 | -0.073208 | 0.0000 | FAIL | NO |
| fremlin:8_18:knot.8_18z | knot | 1 | FAIL | 0.2477 | 0.057261 | -0.1008 | FAIL | NO |
| knotplot:knot_7.1 | knot | 1 | FAIL | 0.2027 | 0.29677 | -0.0388 | FAIL | NO |
| fremlin:8_21:knot.8_21r | knot | 1 | FAIL | 1.0000 | 0.093207 | -0.2475 | FAIL | NO |
| knotplot:torus_3.9 | torus_link | 3 | FAIL | 0.2393 | -0.83548 | 0.0098 | FAIL | NO |
| fremlin:8_6:knot.8_6p | knot | 1 | FAIL | 0.1844 | 2.2662e-12 | -0.0100 | FAIL | NO |
| fremlin:8_14:knot.8_14d | knot | 1 | FAIL | 1.0000 | -0.3949 | -0.1258 | FAIL | NO |
| fremlin:6_3:knot.6_3d | knot | 1 | FAIL | 0.5531 | -0.90149 | 0.0083 | FAIL | NO |
| knotplot:knot_8.17 | knot | 1 | FAIL | 0.1207 | 0.0035021 | 0.0063 | FAIL | NO |
| fremlin:3_1:knot.3_1p | knot | 1 | FAIL | 0.2618 | -0.035423 | -0.0246 | PASS | NO |
| fremlin:8_1:knot.8_1d | knot | 1 | FAIL | 0.4473 | 0.79658 | -0.0650 | FAIL | NO |
| fremlin:7_3:knot.7_3d | knot | 1 | FAIL | 0.6277 | 0.49311 | -0.0238 | FAIL | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
