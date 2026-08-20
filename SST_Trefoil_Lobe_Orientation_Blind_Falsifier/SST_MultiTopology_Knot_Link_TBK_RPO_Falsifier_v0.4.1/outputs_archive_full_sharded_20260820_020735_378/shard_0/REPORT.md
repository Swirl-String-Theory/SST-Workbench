# SST Multi-Topology Panel Report

Overall panel classification: **0_PASS_16_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| fremlin:8_7:knot.8_7d | knot | 1 | FAIL | 0.6062 | 0.0097732 | -0.0117 | FAIL | NO |
| knotplot:torus_6.21 | torus_link | 3 | FAIL | 0.8309 | -4.8125 | -0.0006 | FAIL | NO |
| fremlin:3_1:knot.3_1u | knot | 1 | FAIL | 0.7362 | 0.1519 | 0.0694 | FAIL | NO |
| knotplot:link_0.3.1 | unlink | 3 | FAIL | 0.1758 | 3.7996e-08 | 0.0002 | PASS | NO |
| knotplot:knot_8.18 | knot | 1 | FAIL | 0.2113 | 0.54052 | -0.0218 | FAIL | NO |
| knotplot:knot_7.2 | knot | 1 | FAIL | 0.0648 | 0.05945 | -0.0221 | FAIL | NO |
| fremlin:8_19:knot.8_19t | knot | 1 | FAIL | 0.3283 | 0.0085109 | -0.0271 | FAIL | NO |
| knotplot:torus_2.6 | torus_link | 2 | FAIL | 0.2330 | 0.2992 | -0.0779 | FAIL | NO |
| fremlin:8_3:knot.8_3 | knot | 1 | FAIL | 0.5677 | -0.77669 | -0.0069 | FAIL | NO |
| fremlin:8_10:knot.8_10s | knot | 1 | FAIL | 0.3964 | -1.104e-13 | -0.0167 | FAIL | NO |
| fremlin:5_2:knot.5_2 | knot | 1 | FAIL | 0.1025 | -0.018603 | 0.0044 | FAIL | NO |
| fremlin:6_3:knot.6_3z | knot | 1 | FAIL | 0.7962 | -0.59767 | -0.3212 | FAIL | NO |
| knotplot:knot_4.1 | knot | 1 | FAIL | 0.0896 | -0.042589 | -0.0226 | FAIL | NO |
| fremlin:10_1:knot.10_1 | knot | 1 | FAIL | 0.8281 | 0.2777 | -0.0425 | FAIL | NO |
| fremlin:7_4:knot.7_4 | knot | 1 | FAIL | 0.8268 | -0.24065 | -0.0247 | FAIL | NO |
| fremlin:8_14:knot.8_14r | knot | 1 | FAIL | 0.9443 | -0.73202 | -0.2025 | FAIL | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
