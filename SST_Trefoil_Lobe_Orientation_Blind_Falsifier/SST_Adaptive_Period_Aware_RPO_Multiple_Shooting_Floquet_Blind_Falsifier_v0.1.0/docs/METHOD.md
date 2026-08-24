# METHOD AND FALSIFICATION LOGIC

## Why not change `rpo_return_ratio_max`?

Because that would change the null test after seeing failures. The package instead makes the observation horizon commensurate with the measured oscillation period while retaining the original strict return criteria.

## Why multiple eigenpairs?

v0.4.8 `choose_oscillatory` returns only the first oscillatory eigenpair in descending real-part order. A nonlinear recurrent family need not be tangent to that single pair. This release searches a preregistered number of positive-imaginary pairs and reports every tested domain point.

## Why multiple shooting?

A free trajectory recurrence is a seed detector. Multiple shooting converts a near return into a boundary-value closure test by demanding segment-to-segment continuity. It is harder to pass than merely finding one low recurrence sample.

## What remains unproven?

Even a bounded Floquet RPO in this reduced operational basis is not a proof of continuum Euler stability. High-k spectral convergence and resolution/finite-core certification remain independent obligations.
