# Independence protocol — v0.1.1

## Scientific question

Does a normalized finite-core incompressible periodic vortex-ring system possess a robust internally selected **dimensionless** spectral feature that survives numerical convergence tests?

## Deliberate exclusions

The solver accepts no SI quantity, external physical constant, externally supplied target scale, or model-specific calibration. Length and circulation are nondimensionalized internally as `a=1` and `Gamma=1`.

## Search domain

For the default `R/a=4`, geometric non-overlap requires `q>ln(10)`. The v0.1.1 campaign therefore uses `2.31 <= q <= 4.10`.

This interval is a numerical follow-up to the independent v0.1.0 run; it is not selected from an external physical target.

## Primary observables

1. `spectral_abscissa`;
2. `gap_after_neutral` after dropping the configured number of near-neutral eigenvalues by magnitude;
3. `unstable_count`;
4. `relative_shape_residual`;
5. branch eigenvectors and consecutive phase-invariant overlaps.

## Primary candidate events

- a sign change of `spectral_abscissa`;
- an isolated local minimum of `gap_after_neutral` at least 20% below both adjacent coarse-grid points.

`unstable_count` transitions are reported as secondary multiplicity events.

Neutral-interaction events remain diagnostic but can nominate a candidate only above the fixed finite-difference signal floor gate.

## Automatic refinement

Every primary candidate found by the coarse scan is refined locally. The code receives the coarse candidate list, not a manually supplied q target.

## Convergence promotion

A gap-minimum cluster is promoted as a converged numerical candidate only when:

- N=64 and N=96 agree within 0.02 in q;
- image shells 2 and 3 agree within 0.02 in q;
- at least three finite-difference steps agree with total q-spread below 0.02.

## Blinding rule

No external comparison is implemented. Freeze the complete audit directory with `freeze_results.py` before any external interpretation.
