# SST Multi-Topology Panel Report

Overall panel classification: **8_PASS_9_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| fremlin_3_1 | knot | 1 | PASS | 0.0000 | 0.25532 | 0.0000 | PASS | NO |
| fremlin_5_2 | knot | 1 | FAIL | 0.1241 | -0.098605 | 0.0554 | PASS | NO |
| link_0.3.1 | unlink | 3 | FAIL | 1.0000 | 3.7402e-08 | 0.0455 | PASS | NO |
| knot_5.1 | knot | 1 | PASS | 0.0478 | -0.44924 | -0.0197 | PASS | NO |
| knot_0.1 | unknot | 1 | FAIL | 1.0000 | 0 | -0.0188 | PASS | NO |
| fremlin_5_1 | knot | 1 | PASS | 0.0000 | 0.02887 | 0.0000 | PASS | NO |
| knot_3.1 | knot | 1 | PASS | 0.0001 | -0.052643 | -0.0000 | PASS | NO |
| link_6.3.1 | link | 3 | FAIL | 0.4452 | -0.53894 | -0.1140 | FAIL | NO |
| knot_5.2 | knot | 1 | FAIL | 0.1396 | 0.40983 | 0.1049 | PASS | NO |
| torus_6.9 | torus_link | 3 | FAIL | 1.0000 | -0.58032 | -0.1073 | FAIL | NO |
| link_6.3.3 | link | 3 | FAIL | 0.2438 | -0.87705 | -0.0064 | PASS | NO |
| knot_4.1 | knot | 1 | PASS | 0.0474 | -0.095507 | -0.0066 | PASS | NO |
| fremlin_4_1 | knot | 1 | PASS | 0.0488 | -1.1145e-15 | -0.0039 | PASS | NO |
| fremlin_0_1 | unknot | 1 | FAIL | 1.0000 | 0 | -0.0000 | PASS | NO |
| torus_2.3 | torus_knot | 1 | PASS | 0.0000 | -3.6346e-05 | 0.0000 | PASS | NO |
| link_0.2.1 | unlink | 2 | FAIL | 1.0000 | -8.6176e-14 | -0.0000 | PASS | NO |
| link_2.2.1 | link | 2 | PASS | 0.0079 | 0.089721 | -0.0077 | PASS | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
