# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | knotplot:knot_7.4 | knot | 1 | 0.0519752 | FAIL |
| 2 | knotplot:link_9.2.40 | link | 2 | 0.0571465 | FAIL |
| 3 | knotplot:link_6.3.3 | link | 3 | 0.0648867 | FAIL |
| 4 | knotplot:knot_6.1 | knot | 1 | 0.111794 | FAIL |
| 5 | knotplot:torus_3.3 | torus_link | 3 | 0.119353 | FAIL |
| 6 | fremlin:9_2:knot.9_2n | knot | 1 | 0.120722 | FAIL |
| 7 | knotplot:torus_2.3 | torus_knot | 1 | 0.179139 | FAIL |
| 8 | fremlin:8_17:knot.8_17 | knot | 1 | 0.308857 | FAIL |
| 9 | fremlin:1_1:knot.1_1 | unknot | 1 | 0.319943 | FAIL |
| 10 | fremlin:6_2:knot.6_2d | knot | 1 | 0.334287 | FAIL |
| 11 | fremlin:5_1:knot.5_1 | knot | 1 | 0.354325 | FAIL |
| 12 | fremlin:8_5:knot.8_5 | knot | 1 | 0.429454 | FAIL |
| 13 | fremlin:7_2:knot.7_2r | knot | 1 | 0.551318 | FAIL |
| 14 | fremlin:7_7:knot.7_7d | knot | 1 | 0.851518 | FAIL |
| 15 | fremlin:8_21:knot.8_21d | knot | 1 | 1 | FAIL |
| 16 | fremlin:8_13:knot.8_13d | knot | 1 | 1 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|
| knotplot:link_6.3.3 | +1.00012, -1.00011, +1.00012 | 0.446512 | 6.68e-06 |
| knotplot:link_9.2.40 | -3.00207 | -1.16896 | 5.54e-05 |
| knotplot:torus_3.3 | -1.00009, -1.00009, -1.00009 | -0.245239 | 2e-05 |

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
