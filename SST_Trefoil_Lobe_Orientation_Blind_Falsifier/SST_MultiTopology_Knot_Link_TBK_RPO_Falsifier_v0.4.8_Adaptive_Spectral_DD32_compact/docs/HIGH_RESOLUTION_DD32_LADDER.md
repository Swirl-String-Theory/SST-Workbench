# v0.4.7 High-Resolution DD32 Convergence Ladder

## Purpose

A single larger calculation cannot distinguish spatial-discretization error from spectral truncation. v0.4.7 therefore changes one numerical axis at a time and requires measured-tail support before a convergence conclusion is accepted.

## Preregistered rungs

| rung | N total | Kelvin harmonics | eps used for P1 | robustness eps | dynamics |
|---|---:|---|---|---|---|
| R0 | 360 | 2..8 | .001,.002,.004,.008 | — | linear only |
| R1 | 540 | 2..8 | .001,.002,.004,.008 | — | linear only |
| R2 | 720 | 2..8 | .001,.002,.004,.008 | — | linear only |
| R3 | 720 | 2..12 | .001,.002,.004,.008 | — | linear only |
| R4 | 720 | 2..16 | .001,.002,.004,.008 | — | linear only |
| R5 | 720 | 2..16 | .001,.002,.004,.008 | .012,.016 | full ringdown/RPO/Floquet |

The reduced Jacobian used for normalized growth is always the epsilon=0.004 Jacobian. This prevents a change in the epsilon list from silently changing the object being compared across rungs.

## Spatial tail

Using g0,g1,g2 from R0,R1,R2:

- quasi-monotone: the last two increments have the same sign (within numerical zero),
- contracting: |g2-g1| / |g1-g0| <= 0.85,
- small last step: |g2-g1| / max(|g2|,0.12) <= 0.05,
- P2 verdict must be stable across the three rungs.

## Spectral tail

Using R2,R3,R4 at fixed N=720, the same tail tests are applied. In addition, the requested k_max basis must still be present after rigid-removal/orthonormalization, and the squared coefficient weight of the dominant-growth eigenvector on Kelvin modes at the active k_max must be <= 0.15. A large boundary weight is an explicit `UNRESOLVED` marker because the dominant mode may be trying to leave the truncated basis.

## Extrapolation discipline

A diagnostic fit

    g(N) = g_inf + c N^(-p)

is scanned over 0.25 <= p <= 4.0. The fit is *never* accepted merely because its residual is small. `tail_supported=true` additionally requires measured spatial-tail convergence and stable P2 verdicts. This mirrors the theorem-style discipline used in the trefoil robustness work: a formal asymptotic fit without a contracting high-resolution tail is not enough.

## Large-epsilon robustness

R5 evaluates eps=.012,.016 but these values do not enter P1. Instead the package records

    ||J(eps)-J(.004)||_F / ||J(.004)||_F

as a finite-amplitude robustness diagnostic. A drift above 0.25 is a warning/FP64-confirmation reason, not an automatic failure of the local linear gate.

## Final synthesis

A dataset is `CONVERGED_PASS` or `CONVERGED_FAIL` only if spatial and spectral tails converge, P2 verdicts remain stable, and the dominant eigenmode does not pile up at k_max. Otherwise it is `UNRESOLVED`.

DD32 is not IEEE FP64. The automatic confirmation queue includes unresolved cases, all converged passes, values within 0.02 of g=0.12, large-epsilon warnings, k_max-boundary cases, and any RPO/Floquet candidate.
