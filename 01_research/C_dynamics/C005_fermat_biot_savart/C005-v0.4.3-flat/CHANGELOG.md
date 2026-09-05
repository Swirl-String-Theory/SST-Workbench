# Changelog

## v0.4.3 — Threshold Censoring and Clock-Domain Metadata

- Preserved the v0.4.2 clock-safe root-refinement hotfix.
- Added explicit clock-boundary brackets and connected real-clock component counts per sampled ray.
- Corrected `valid_clock_ray_count` to mean rays with at least one valid probe; retained a separate `fully_clock_valid_ray_count`.
- Added `candidate_surface_fraction_valid_clock_rays`, `candidate_surface_fraction_all_rays`, and the fully-valid conditional fraction.
- Replaced ambiguous sampled onset/loss labels with first/last-present values, censoring flags, and present/absent brackets.
- Added regression checks for the split-clock-domain control case at `epsilon/r_c=0.0010`.
- Preserved all global closed-orbit and QSM guards.

## v0.4.2 — Clock-Domain Root-Refinement Hotfix

- Rejected brackets whose bisection midpoint leaves the real clock domain.
- Evaluated endpoint derivatives using endpoint `S` values instead of the root-point denominator.
- Prevented complex values from `(1-beta^2)^(3/2)` in clock-invalid regions.
- Kept clock-boundary brackets separate from stationary roots.

## v0.4.1 — Campaign Automation and Certification Corrections

- Corrected candidate-fraction normalization and pre-convergence root labels.
- Added the missing high-resolution `3_1` convergence ladder.
- Added adaptive bifurcation and scale-sweep resolution planning.
- Added resumable campaign execution, logging, ZIP packaging, and SHA-256 output.

## v0.4.0 — Candidate Certification and Bifurcation Atlas

- Added analytic regularized Biot--Savart field Jacobians in C++ and Python.
- Added `biot_savart_batch_with_jacobian` to the pybind11 interface.
- Replaced sampled-minimum detection for v0.4 claims with a bracketed solver for
  \(G=1-\beta^2+\rho\,\boldsymbol\beta\cdot\partial_\rho\boldsymbol\beta=0\).
- Added radial stationary-root classification and orbit-seed output.
- Added three-level candidate convergence reports.
- Added softening bifurcation branch tracking.
- Added independent ideal-knot scale sweeps.
- Added approximate curvature/DCSD reach diagnostics with explicit non-rigorous status.
- Added translation, rotation, reindexing, orientation-reversal, and mirror covariance audits.
- Added field and Jacobian native/Python parity gates to `run_all_checks.py`.
- Preserved the four-knot matrix \(0_1,3_1,4_1,5_2\).
- Preserved all guards against claiming global closed Fermat orbits or QSM poles.

## v0.3.0

- Added adaptive centerline resolution, softening matrices, profile matrices, and fixed-probe convergence ladders.
- Added the exact straight Rosenhead horizon and critical thresholds.

## v0.2.0

- Added the four ideal-knot Fourier centerlines and native/Python full-field parity matrix.

## v0.1.1

- Fixed setuptools flat-layout discovery for local pybind11 builds.

## v0.1.0

- Initial standalone radial profile and regularized Biot--Savart research harness.
