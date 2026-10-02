# Changelog

## v0.4.2

- Fixed the v0.4.1 bifurcation crash caused by fractional powers of negative `S^2`.
- Added strict clock-domain gating before every `S^{-1}` or `S^{-3}` evaluation.
- Added `CLOCK_BOUNDARY_BRACKET` and refinement-domain diagnostics.
- Added the exact Jacobian of the discretized Rosenhead midpoint kernel in Python and C++.
- Added direct stationary-root resolution using `G = S^2 + rho beta·(J beta e_rho)`.
- Added candidate-atlas, convergence, bifurcation, scale-sweep, symmetry-audit, and campaign CLIs.
- Added three-level weak/strong convergence classification.
- Added non-rigorous curvature + approximate-dcsd reach diagnostics with explicit guards.
- Added chunked Fourier evaluation for large adaptive centerlines.
- Preserved all global-orbit and QSM non-certification guards.
- Reconstructed from the available v0.3.0 source and the uploaded v0.4.1 results/CLI record; no exact v0.4.1 source archive was available.

## v0.3.0

- Added adaptive per-knot centerline resolution and softening studies.
- Added the four-knot matrix `0_1`, `3_1`, `4_1`, and `5_2`.
- Added exact straight-reference Rosenhead horizon and critical thresholds.
- Added resolution ladders and Python/C++ field parity diagnostics.
