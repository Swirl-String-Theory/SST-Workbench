# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | knotplot:knot_7.2 | knot | 1 | 0.0648361 | FAIL |
| 2 | knotplot:knot_4.1 | knot | 1 | 0.089581 | FAIL |
| 3 | fremlin:5_2:knot.5_2 | knot | 1 | 0.102469 | FAIL |
| 4 | knotplot:link_0.3.1 | unlink | 3 | 0.175794 | FAIL |
| 5 | knotplot:knot_8.18 | knot | 1 | 0.211315 | FAIL |
| 6 | knotplot:torus_2.6 | torus_link | 2 | 0.233024 | FAIL |
| 7 | fremlin:8_19:knot.8_19t | knot | 1 | 0.32831 | FAIL |
| 8 | fremlin:8_10:knot.8_10s | knot | 1 | 0.396446 | FAIL |
| 9 | fremlin:8_3:knot.8_3 | knot | 1 | 0.567688 | FAIL |
| 10 | fremlin:8_7:knot.8_7d | knot | 1 | 0.606218 | FAIL |
| 11 | fremlin:3_1:knot.3_1u | knot | 1 | 0.736235 | FAIL |
| 12 | fremlin:6_3:knot.6_3z | knot | 1 | 0.796155 | FAIL |
| 13 | fremlin:7_4:knot.7_4 | knot | 1 | 0.826751 | FAIL |
| 14 | fremlin:10_1:knot.10_1 | knot | 1 | 0.82809 | FAIL |
| 15 | knotplot:torus_6.21 | torus_link | 3 | 0.830899 | FAIL |
| 16 | fremlin:8_14:knot.8_14r | knot | 1 | 0.944268 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|
| knotplot:torus_6.21 | -14.03167, -14.02736, -14.03167 | -4.81251 | 0 |
| knotplot:link_0.3.1 | +0.00000, +0.00000, -0.00000 | 3.7996e-08 | 1.59e-09 |
| knotplot:torus_2.6 | -3.00133 | 0.299197 | 0.000296 |

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
