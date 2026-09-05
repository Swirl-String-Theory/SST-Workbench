# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | knotplot:link_8.2.1 | link | 2 | 0.0374613 | FAIL |
| 2 | knotplot:link_7.2.5 | link | 2 | 0.0635325 | FAIL |
| 3 | knotplot:link_4.2.1 | link | 2 | 0.0908637 | PASS |
| 4 | fremlin:10_1:knot.10_1n | knot | 1 | 0.107609 | FAIL |
| 5 | knotplot:knot_10.1 | knot | 1 | 0.117457 | FAIL |
| 6 | fremlin:7_5:knot.7_5 | knot | 1 | 0.124015 | FAIL |
| 7 | knotplot:link_6.2.1 | link | 2 | 0.194069 | FAIL |
| 8 | fremlin:8_7:knot.8_7s | knot | 1 | 0.260976 | FAIL |
| 9 | fremlin:5_2:knot.5_2d | knot | 1 | 0.308181 | FAIL |
| 10 | fremlin:4_1:knot.4_1 | knot | 1 | 0.326383 | FAIL |
| 11 | fremlin:8_11:knot.8_11 | knot | 1 | 0.335297 | FAIL |
| 12 | knotplot:torus_2.7 | torus_knot | 1 | 0.359241 | FAIL |
| 13 | fremlin:7_1:knot.7_1 | knot | 1 | 0.362008 | FAIL |
| 14 | fremlin:8_3:knot.8_3d | knot | 1 | 0.44179 | FAIL |
| 15 | fremlin:8_19:knot.8_19u | knot | 1 | 0.879157 | FAIL |
| 16 | fremlin:8_15:knot.8_15 | knot | 1 | 1 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|
| knotplot:link_6.2.1 | +3.00126 | -0.0732159 | 6.81e-05 |
| knotplot:link_8.2.1 | -4.00274 | -1.13241 | 2.09e-05 |
| knotplot:link_7.2.5 | +2.00101 | 1.13651 | 0 |
| knotplot:link_4.2.1 | -2.00040 | 0.602843 | 2.36e-06 |

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
