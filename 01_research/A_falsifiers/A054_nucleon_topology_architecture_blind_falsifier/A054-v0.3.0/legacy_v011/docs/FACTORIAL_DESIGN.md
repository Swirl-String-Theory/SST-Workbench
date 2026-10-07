# Full-factorial design matrix

## Reveal-only semantic axes

| axis | levels |
|---|---|
| skeleton | `U` unlinked, `G` T(3,3), `B` Borromean |
| component slot 0 | `5_2`, `6_1` |
| component slot 1 | `5_2`, `6_1` |
| component slot 2 | `5_2`, `6_1` |
| relative polarity | `+++`, `-++`, `+-+`, `++-` modulo global reversal |
| circulation normalization | per-component quantum, fixed-total equal split |
| provider stratum | Cartesian E011 `5_2 x 6_1` provider-anchor envelope |

The three binary component factors form an 8-vertex cube. Each directed cube edge is a single-site substitution

\[
5_2 \rightarrow 6_1
\]

with all other factors held fixed.

## Mixed composition classes

The three assignments with exactly one `6_1` are the complete position-permutation family of

\[
5_2+5_2+6_1.
\]

The three assignments with exactly two `6_1` are the complete position-permutation family of

\[
5_2+6_1+6_1.
\]

This prevents a skeleton slot or polarity slot from being silently confounded with the historical `uud`/`udd` composition interpretation.

## Primary interaction test

For each factor cell and normalization, define

\[
\Delta_j S_{\times}=S_{\times}^{(2+1,j)}-S_{\times}^{(+++)},
\]

where slot \(j\) is the one with reversed circulation. After reveal, the same values are grouped by whether slot \(j\) contains `5_2` or `6_1`. Therefore the key interaction is directly observable:

\[
\text{knot identity at reversed slot}\times\text{polarity benefit}.
\]

No particle label enters that calculation.
