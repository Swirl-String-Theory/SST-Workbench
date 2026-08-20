# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | fremlin_5_1 | knot | 1 | 6.91149e-07 | PASS |
| 2 | torus_2.3 | torus_knot | 1 | 1.14278e-06 | PASS |
| 3 | fremlin_3_1 | knot | 1 | 1.8663e-05 | PASS |
| 4 | knot_3.1 | knot | 1 | 0.000102636 | PASS |
| 5 | link_2.2.1 | link | 2 | 0.00793726 | PASS |
| 6 | knot_4.1 | knot | 1 | 0.0474121 | PASS |
| 7 | knot_5.1 | knot | 1 | 0.0478339 | PASS |
| 8 | fremlin_4_1 | knot | 1 | 0.0487833 | PASS |
| 9 | fremlin_5_2 | knot | 1 | 0.124103 | FAIL |
| 10 | knot_5.2 | knot | 1 | 0.139578 | FAIL |
| 11 | link_6.3.3 | link | 3 | 0.243843 | FAIL |
| 12 | link_6.3.1 | link | 3 | 0.44522 | FAIL |
| 13 | fremlin_0_1 | unknot | 1 | 1 | FAIL |
| 14 | knot_0.1 | unknot | 1 | 1 | FAIL |
| 15 | link_0.3.1 | unlink | 3 | 1 | FAIL |
| 16 | torus_6.9 | torus_link | 3 | 1 | FAIL |
| 17 | link_0.2.1 | unlink | 2 | 1 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|
| link_0.3.1 | +0.00000, +0.00000, -0.00000 | 3.74025e-08 | 6.96e-10 |
| link_6.3.1 | -1.00025, -1.00026, +1.00024 | -0.538937 | 0.000246 |
| torus_6.9 | -6.00352, -6.00327, -6.00350 | -0.580315 | 0 |
| link_6.3.3 | +1.00012, -1.00011, +1.00012 | -0.877046 | 0.000262 |
| link_0.2.1 | -0.00000 | -8.6141e-14 | 1.63e-10 |
| link_2.2.1 | +1.00007 | 0.0897207 | 6.85e-06 |

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
