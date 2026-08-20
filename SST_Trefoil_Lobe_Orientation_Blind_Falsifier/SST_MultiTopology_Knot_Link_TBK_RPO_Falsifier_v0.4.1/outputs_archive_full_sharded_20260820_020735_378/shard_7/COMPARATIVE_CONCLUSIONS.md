# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | knotplot:knot_6.2 | knot | 1 | 0.1192 | FAIL |
| 2 | knotplot:knot_8.17 | knot | 1 | 0.12065 | FAIL |
| 3 | fremlin:8_6:knot.8_6p | knot | 1 | 0.184364 | FAIL |
| 4 | knotplot:knot_7.1 | knot | 1 | 0.202715 | FAIL |
| 5 | knotplot:torus_3.9 | torus_link | 3 | 0.239276 | FAIL |
| 6 | knotplot:link_0.2.1 | unlink | 2 | 0.241916 | FAIL |
| 7 | fremlin:8_18:knot.8_18z | knot | 1 | 0.247652 | FAIL |
| 8 | fremlin:3_1:knot.3_1p | knot | 1 | 0.261836 | FAIL |
| 9 | knotplot:torus_2.5 | torus_knot | 1 | 0.280334 | FAIL |
| 10 | fremlin:8_1:knot.8_1d | knot | 1 | 0.447323 | FAIL |
| 11 | fremlin:6_3:knot.6_3d | knot | 1 | 0.553055 | FAIL |
| 12 | fremlin:7_3:knot.7_3d | knot | 1 | 0.62772 | FAIL |
| 13 | fremlin:8_21:knot.8_21r | knot | 1 | 1 | FAIL |
| 14 | fremlin:8_14:knot.8_14d | knot | 1 | 1 | FAIL |
| 15 | fremlin:5_1:knot.5_1u | knot | 1 | 1 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|
| knotplot:link_0.2.1 | -0.00000 | 4.62442e-13 | 8.17e-11 |
| knotplot:torus_3.9 | -3.00128, -3.00121, -3.00126 | -0.835477 | 0.000136 |

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
