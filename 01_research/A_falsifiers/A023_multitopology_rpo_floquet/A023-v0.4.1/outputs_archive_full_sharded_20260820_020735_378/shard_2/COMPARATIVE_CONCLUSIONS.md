# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | fremlin:12a_1202:knot.12a_1202 | knot | 1 | 0.0692317 | FAIL |
| 2 | knotplot:link_7.2.6 | link | 2 | 0.0861379 | FAIL |
| 3 | knotplot:knot_6.3 | knot | 1 | 0.119928 | FAIL |
| 4 | knotplot:knot_5.1 | knot | 1 | 0.217407 | FAIL |
| 5 | fremlin:8_11:knot.8_11d | knot | 1 | 0.249663 | FAIL |
| 6 | fremlin:8_2:knot.8_2 | knot | 1 | 0.252319 | FAIL |
| 7 | knotplot:torus_2.8 | torus_link | 2 | 0.261486 | FAIL |
| 8 | knotplot:knot_9.1 | knot | 1 | 0.297956 | FAIL |
| 9 | knotplot:knot_10.123 | knot | 1 | 0.307157 | FAIL |
| 10 | fremlin:8_8:knot.8_8d | knot | 1 | 0.344667 | FAIL |
| 11 | fremlin:7_5:knot.7_5d | knot | 1 | 0.435796 | FAIL |
| 12 | fremlin:8_3:knot.8_3z | knot | 1 | 0.445257 | FAIL |
| 13 | fremlin:7_1:knot.7_1p | knot | 1 | 0.534463 | FAIL |
| 14 | fremlin:4_1:knot.4_1d | knot | 1 | 0.595999 | FAIL |
| 15 | fremlin:5_2:knot.5_2r | knot | 1 | 0.645955 | FAIL |
| 16 | fremlin:8_15:knot.8_15d | knot | 1 | 1 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|
| knotplot:link_7.2.6 | +0.00028 | 2.38213 | 6.28e-05 |
| knotplot:torus_2.8 | -4.00306 | 0.146601 | 0.000788 |

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
