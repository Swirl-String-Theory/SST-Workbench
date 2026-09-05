# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | knotplot:knot_5.2 | knot | 1 | 0.0412668 | FAIL |
| 2 | fremlin:7_2:knot.7_2 | knot | 1 | 0.0862953 | FAIL |
| 3 | knotplot:link_6.3.1 | link | 3 | 0.114129 | FAIL |
| 4 | knotplot:knot_9.2 | knot | 1 | 0.166182 | FAIL |
| 5 | fremlin:8_12:knot.8_12d | knot | 1 | 0.177653 | FAIL |
| 6 | knotplot:link_7.2.8 | link | 2 | 0.19054 | FAIL |
| 7 | fremlin:6_1:knot.6_1 | knot | 1 | 0.199734 | FAIL |
| 8 | knotplot:torus_2.9 | torus_knot | 1 | 0.297978 | FAIL |
| 9 | fremlin:12a_1202:knot.12a_1202z6 | knot | 1 | 0.342018 | FAIL |
| 10 | knotplot:torus_2.11 | torus_knot | 1 | 0.466137 | FAIL |
| 11 | fremlin:7_6:knot.7_6d | knot | 1 | 0.536373 | FAIL |
| 12 | fremlin:8_15:knot.8_15p | knot | 1 | 0.578926 | FAIL |
| 13 | fremlin:4_1:knot.4_1p | knot | 1 | 0.862654 | FAIL |
| 14 | fremlin:8_4:knot.8_4 | knot | 1 | 1 | FAIL |
| 15 | fremlin:8_9:knot.8_9d | knot | 1 | 1 | FAIL |
| 16 | fremlin:8_2:knot.8_2d | knot | 1 | 1 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|
| knotplot:link_6.3.1 | -1.00025, -1.00026, +1.00024 | 0.52506 | 5.01e-05 |
| knotplot:link_7.2.8 | +0.00001 | -0.44931 | 4.78e-06 |

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
