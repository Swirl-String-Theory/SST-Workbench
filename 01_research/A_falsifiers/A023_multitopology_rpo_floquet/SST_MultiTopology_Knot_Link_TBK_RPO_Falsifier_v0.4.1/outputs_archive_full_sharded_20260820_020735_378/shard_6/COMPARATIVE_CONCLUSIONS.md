# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | knotplot:knot_9.35 | knot | 1 | 0.0899598 | FAIL |
| 2 | knotplot:knot_8.1 | knot | 1 | 0.142961 | FAIL |
| 3 | knotplot:torus_2.4 | torus_link | 2 | 0.163059 | FAIL |
| 4 | fremlin:8_6:knot.8_6 | knot | 1 | 0.216158 | FAIL |
| 5 | fremlin:7_3:knot.7_3 | knot | 1 | 0.235202 | FAIL |
| 6 | fremlin:3_1:knot.3_1 | knot | 1 | 0.257438 | FAIL |
| 7 | knotplot:knot_0.1 | unknot | 1 | 0.319463 | FAIL |
| 8 | fremlin:5_1:knot.5_1p | knot | 1 | 0.35036 | FAIL |
| 9 | knotplot:torus_6.9 | torus_link | 3 | 0.385036 | FAIL |
| 10 | fremlin:6_2:knot.6_2p | knot | 1 | 0.41586 | FAIL |
| 11 | knotplot:torus_3.6 | torus_link | 3 | 0.428852 | FAIL |
| 12 | fremlin:8_1:knot.8_1 | knot | 1 | 0.471327 | FAIL |
| 13 | fremlin:8_18:knot.8_18 | knot | 1 | 0.493787 | FAIL |
| 14 | knotplot:torus_6.15 | torus_link | 3 | 0.523461 | FAIL |
| 15 | fremlin:8_21:knot.8_21p | knot | 1 | 0.87253 | FAIL |
| 16 | fremlin:8_13:knot.8_13p | knot | 1 | 0.976697 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|
| knotplot:torus_6.9 | -6.00352, -6.00327, -6.00350 | 1.48219 | 0 |
| knotplot:torus_2.4 | -2.00042 | -0.212197 | 3.42e-05 |
| knotplot:torus_3.6 | -2.00046, -2.00046, -2.00046 | 0.707601 | 7.6e-05 |
| knotplot:torus_6.15 | -10.01346, -10.01279, -10.01332 | -1.30527 | 0 |

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
