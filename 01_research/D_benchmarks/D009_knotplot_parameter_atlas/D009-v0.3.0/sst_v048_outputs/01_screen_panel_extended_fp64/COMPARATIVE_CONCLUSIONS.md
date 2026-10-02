# Comparative Conclusions

These comparisons are generated only after unblinding and do not alter any gate threshold.

## Linear-growth ranking

| rank | source | class | components | normalized growth | status |
|---:|---|---|---:|---:|---|
| 1 | hooke__0p25 | knot | 1 | 0.000594635 | FAIL |
| 2 | amfpower__1 | knot | 1 | 0.00113305 | FAIL |
| 3 | charge__60 | knot | 1 | 0.00164261 | PASS |
| 4 | hooke__0p5 | knot | 1 | 0.00249077 | PASS |
| 5 | amechforce__on | knot | 1 | 0.00249342 | FAIL |
| 6 | thfstrength__0p02 | knot | 1 | 0.00543622 | PASS |
| 7 | thfstrength__0p04 | knot | 1 | 0.0128024 | FAIL |
| 8 | thermalforce__on | knot | 1 | 0.0821713 | PASS |
| 9 | amfpower__4 | knot | 1 | 0.122817 | FAIL |
| 10 | tinc__3p75 | knot | 1 | 0.1247 | FAIL |
| 11 | sytmag__4 | knot | 1 | 0.132908 | FAIL |
| 12 | thfstrength__0p01 | knot | 1 | 0.137741 | FAIL |
| 13 | syfmag__1 | knot | 1 | 0.13908 | FAIL |
| 14 | syrmag__4 | knot | 1 | 0.150617 | FAIL |
| 15 | syfmag__4 | knot | 1 | 0.150932 | FAIL |
| 16 | tinc__60 | knot | 1 | 0.151273 | FAIL |
| 17 | sytmag__0p25 | knot | 1 | 0.15144 | FAIL |
| 18 | mechforce__on | knot | 1 | 0.163243 | FAIL |
| 19 | bencon__0p25 | knot | 1 | 0.16327 | FAIL |
| 20 | bencon__1 | knot | 1 | 0.163351 | FAIL |
| 21 | bencon__4 | knot | 1 | 0.163705 | FAIL |
| 22 | thfstrength__0p0025 | knot | 1 | 0.167033 | FAIL |
| 23 | tanmag__0p025 | knot | 1 | 0.208785 | FAIL |
| 24 | syfmag__0p25 | knot | 1 | 0.20917 | FAIL |
| 25 | power__3 | knot | 1 | 0.211938 | FAIL |
| 26 | syrmag__0p25 | knot | 1 | 0.220714 | FAIL |
| 27 | tanforce__on | knot | 1 | 0.344194 | FAIL |
| 28 | charge__3p75 | knot | 1 | 0.407173 | FAIL |
| 29 | power__7 | knot | 1 | 0.420047 | FAIL |
| 30 | tanmag__0p4 | knot | 1 | 0.433345 | FAIL |
| 31 | elecforce__off | knot | 1 | 0.471224 | FAIL |
| 32 | hooke__4 | knot | 1 | 0.502173 | FAIL |
| 33 | mechforce__off | knot | 1 | 0.969008 | FAIL |

## Link topology diagnostics

| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |
|---|---|---:|---:|

## Interpretation guardrails

- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.
- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.
- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.
- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.
