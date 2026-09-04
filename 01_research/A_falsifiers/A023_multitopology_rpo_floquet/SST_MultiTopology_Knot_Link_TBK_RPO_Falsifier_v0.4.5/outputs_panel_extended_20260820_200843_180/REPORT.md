# SST Multi-Topology Panel Report

Overall panel classification: **3_PASS_14_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| fremlin_3_1 | knot | 1 | FAIL | 0.3185 | -0.25547 | -0.0659 | PASS | NO |
| fremlin_5_2 | knot | 1 | PASS | 0.1143 | -0.065608 | 0.0041 | PASS | NO |
| link_0.3.1 | unlink | 3 | FAIL | 0.7541 | 3.6619e-08 | 0.0008 | PASS | NO |
| knot_5.1 | knot | 1 | FAIL | 0.1774 | -0.46666 | -0.0377 | PASS | NO |
| knot_0.1 | unknot | 1 | FAIL | 0.5358 | 0 | -0.0157 | PASS | NO |
| fremlin_5_1 | knot | 1 | FAIL | 0.2224 | -0.36293 | -0.0000 | FAIL | NO |
| knot_3.1 | knot | 1 | FAIL | 0.2307 | 0.087605 | -0.0655 | PASS | NO |
| link_6.3.1 | link | 3 | FAIL | 0.1545 | 0.53515 | -0.0240 | FAIL | NO |
| knot_5.2 | knot | 1 | PASS | 0.0454 | 0.41355 | 0.0299 | PASS | NO |
| torus_6.9 | torus_link | 3 | FAIL | 0.9396 | 0.52153 | -0.0947 | FAIL | NO |
| link_6.3.3 | link | 3 | FAIL | 0.2253 | -0.97596 | -0.1111 | FAIL | NO |
| knot_4.1 | knot | 1 | FAIL | 0.1728 | -0.040495 | -0.0551 | FAIL | NO |
| fremlin_4_1 | knot | 1 | FAIL | 0.4141 | 0.28421 | -0.0125 | FAIL | NO |
| fremlin_0_1 | unknot | 1 | FAIL | 0.5359 | 0 | -0.0000 | PASS | NO |
| torus_2.3 | torus_knot | 1 | FAIL | 0.2366 | 0.084713 | -0.0655 | PASS | NO |
| link_0.2.1 | unlink | 2 | FAIL | 1.0000 | -6.271e-14 | 0.0000 | PASS | NO |
| link_2.2.1 | link | 2 | PASS | 0.0368 | 0.05461 | -0.0188 | PASS | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
