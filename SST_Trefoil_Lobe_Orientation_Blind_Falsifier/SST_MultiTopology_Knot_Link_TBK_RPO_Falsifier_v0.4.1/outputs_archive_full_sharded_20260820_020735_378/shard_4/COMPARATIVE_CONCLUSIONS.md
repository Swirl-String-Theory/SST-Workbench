# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | fremlin:15331:knot.15331 | knot | 1 | 0.0406954 | FAIL |
| 2 | knotplot:link_5.2.1 | link | 2 | 0.0512023 | FAIL |
| 3 | knotplot:link_2.2.1 | link | 2 | 0.0575389 | PASS |
| 4 | knotplot:link_9.2.20 | link | 2 | 0.062674 | FAIL |
| 5 | knotplot:link_6.3.2 | link | 3 | 0.06853 | FAIL |
| 6 | knotplot:knot_7.3 | knot | 1 | 0.12584 | FAIL |
| 7 | fremlin:6_2:knot.6_2 | knot | 1 | 0.169803 | FAIL |
| 8 | knotplot:knot_3.1 | knot | 1 | 0.174717 | FAIL |
| 9 | fremlin:8_16:knot.8_16 | knot | 1 | 0.309116 | FAIL |
| 10 | fremlin:7_6:knot.7_6s | knot | 1 | 0.393855 | FAIL |
| 11 | fremlin:4_1:knot.4_1z | knot | 1 | 0.513789 | FAIL |
| 12 | fremlin:7_2:knot.7_2d | knot | 1 | 0.847464 | FAIL |
| 13 | fremlin:8_12:knot.8_12z | knot | 1 | 1 | FAIL |
| 14 | fremlin:9_2:knot.9_2 | knot | 1 | 1 | FAIL |
| 15 | fremlin:8_20:knot.8_20r | knot | 1 | 1 | FAIL |
| 16 | fremlin:8_4:knot.8_4d | knot | 1 | 1 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|
| knotplot:link_6.3.2 | -0.00008, +0.00008, -0.00009 | 1.1552 | 2.32e-05 |
| knotplot:link_2.2.1 | +1.00007 | -0.0431147 | 7.12e-06 |
| knotplot:link_9.2.20 | +3.00207 | -0.653598 | 6e-05 |
| knotplot:link_5.2.1 | +0.00000 | 0.17496 | 1.67e-05 |

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
