# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | link_2.2.1 | link | 2 | 0.0367957 | PASS |
| 2 | knot_5.2 | knot | 1 | 0.0453714 | PASS |
| 3 | fremlin_5_2 | knot | 1 | 0.114324 | PASS |
| 4 | link_6.3.1 | link | 3 | 0.154542 | FAIL |
| 5 | knot_4.1 | knot | 1 | 0.172789 | FAIL |
| 6 | knot_5.1 | knot | 1 | 0.177396 | FAIL |
| 7 | fremlin_5_1 | knot | 1 | 0.222365 | FAIL |
| 8 | link_6.3.3 | link | 3 | 0.225283 | FAIL |
| 9 | knot_3.1 | knot | 1 | 0.230682 | FAIL |
| 10 | torus_2.3 | torus_knot | 1 | 0.236552 | FAIL |
| 11 | fremlin_3_1 | knot | 1 | 0.31852 | FAIL |
| 12 | fremlin_4_1 | knot | 1 | 0.414061 | FAIL |
| 13 | knot_0.1 | unknot | 1 | 0.535765 | FAIL |
| 14 | fremlin_0_1 | unknot | 1 | 0.535877 | FAIL |
| 15 | link_0.3.1 | unlink | 3 | 0.754064 | FAIL |
| 16 | torus_6.9 | torus_link | 3 | 0.939618 | FAIL |
| 17 | link_0.2.1 | unlink | 2 | 1 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|
| link_0.3.1 | +0.00000, +0.00000, -0.00000 | 3.66188e-08 | 3.72e-09 |
| link_6.3.1 | -1.00025, -1.00026, +1.00024 | 0.535153 | 0.000174 |
| torus_6.9 | -6.00352, -6.00327, -6.00350 | 0.521534 | 0 |
| link_6.3.3 | +1.00012, -1.00011, +1.00012 | -0.975956 | 3.61e-05 |
| link_0.2.1 | -0.00000 | -6.27098e-14 | 6.73e-10 |
| link_2.2.1 | +1.00007 | 0.0546096 | 3.47e-06 |

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
