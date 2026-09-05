# Changelog

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
