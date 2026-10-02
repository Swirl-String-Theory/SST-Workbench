# SST Multi-Topology Panel Report

Overall panel classification: **1_PASS_15_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| fremlin:9_2:knot.9_2 | knot | 1 | FAIL | 1.0000 | -1.5949 | 0.0056 | FAIL | NO |
| knotplot:link_6.3.2 | link | 3 | FAIL | 0.0685 | 1.1552 | -0.0036 | FAIL | NO |
| fremlin:4_1:knot.4_1z | knot | 1 | FAIL | 0.5138 | 0.23162 | 0.0028 | FAIL | NO |
| knotplot:link_2.2.1 | link | 2 | PASS | 0.0575 | -0.043115 | 0.0018 | PASS | NO |
| knotplot:link_9.2.20 | link | 2 | FAIL | 0.0627 | -0.6536 | -0.0073 | FAIL | NO |
| knotplot:knot_7.3 | knot | 1 | FAIL | 0.1258 | 0.35048 | -0.0075 | FAIL | NO |
| fremlin:8_20:knot.8_20r | knot | 1 | FAIL | 1.0000 | -3.3882e-14 | -0.1230 | FAIL | NO |
| knotplot:knot_3.1 | knot | 1 | FAIL | 0.1747 | -0.059442 | -0.0355 | PASS | NO |
| fremlin:8_4:knot.8_4d | knot | 1 | FAIL | 1.0000 | 0.46945 | -0.1545 | FAIL | NO |
| fremlin:8_12:knot.8_12z | knot | 1 | FAIL | 1.0000 | 0.086907 | 0.0243 | FAIL | NO |
| fremlin:6_2:knot.6_2 | knot | 1 | FAIL | 0.1698 | 5.2939e-14 | -0.0249 | FAIL | NO |
| fremlin:7_2:knot.7_2d | knot | 1 | FAIL | 0.8475 | -0.23243 | -0.0993 | FAIL | NO |
| knotplot:link_5.2.1 | link | 2 | FAIL | 0.0512 | 0.17496 | -0.0058 | FAIL | NO |
| fremlin:15331:knot.15331 | knot | 1 | FAIL | 0.0407 | -9.1658e-15 | -0.0016 | FAIL | NO |
| fremlin:7_6:knot.7_6s | knot | 1 | FAIL | 0.3939 | 0.66128 | -0.0183 | FAIL | NO |
| fremlin:8_16:knot.8_16 | knot | 1 | FAIL | 0.3091 | -6.3405e-14 | -0.0031 | FAIL | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
