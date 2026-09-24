# Independence protocol — preregistered before the run

## Scientific question
Does a normalized, finite-core, incompressible vortex-ring lattice exhibit any internally selected dimensionless cell scale through a robust spectral event?

## Deliberate exclusions
The solver accepts no SI quantity, no external physical constant, no externally supplied target scale, and no model-specific calibration. Length is nondimensionalized by the generic core radius `a`, fixed internally to exactly 1. Circulation is a time unit, fixed internally to exactly 1.

## Primary scan variable
`q = ln(L/a)`, where `L` is the periodic cell size. The scan is uniform in q.

## Preregistered observables
1. `gap_after_neutral`: magnitude of the first eigenvalue after removing six isolated-ring neutral/near-neutral modes.
2. `spectral_abscissa`: maximum real part of the projected shape Jacobian spectrum.
3. `unstable_count`: number of eigenvalues with real part above the numerical tolerance.
4. `relative_shape_residual`: residual internal motion after best-fit translation and rigid rotation removal.

## Candidate events
A scale candidate is reported automatically only when either:
- `unstable_count` changes between adjacent accepted scan points; or
- `gap_after_neutral` has an isolated local minimum at least 20% below both adjacent points.

A candidate is not a derivation. It must survive resolution, finite-difference, image-shell, core-model and geometry tests.

## Equilibrium gate
Spectral interpretation is accepted only if `relative_shape_residual <= residual_max`. Rows failing this gate are still reported but cannot nominate candidates.

## Blinding rule
Do not compare the produced `q`, `L/a`, gaps, or candidate locations with any external theory or target until `audit_out/` has been archived or hashed. This package contains no comparison routine by design.
