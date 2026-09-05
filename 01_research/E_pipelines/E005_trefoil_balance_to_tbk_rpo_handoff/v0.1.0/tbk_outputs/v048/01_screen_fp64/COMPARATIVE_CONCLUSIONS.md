# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | BALX_002 | knot | 1 | 0.159279 | FAIL |
| 2 | BALX_001 | knot | 1 | 0.211137 | FAIL |
| 3 | BALX_007 | knot | 1 | 0.271915 | FAIL |
| 4 | BALX_004 | knot | 1 | 0.292935 | FAIL |
| 5 | BALX_008 | knot | 1 | 0.52758 | FAIL |
| 6 | BALX_003 | knot | 1 | 0.555648 | FAIL |
| 7 | BALX_006 | knot | 1 | 0.591178 | FAIL |
| 8 | BALX_005 | knot | 1 | 0.602711 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
