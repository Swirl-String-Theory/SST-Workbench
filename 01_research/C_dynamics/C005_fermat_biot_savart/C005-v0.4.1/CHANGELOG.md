# Changelog

## v0.4.1 — Campaign Automation and Certification Corrections

- Corrected `candidate_surface_fraction` so it is always normalized by all sampled rays and therefore remains in \([0,1]\).
- Added a separate fraction conditional on fully clock-valid rays.
- Renamed the pre-convergence root label to `RESOLVED_LOCAL_MINIMUM`.
- Added the missing high-resolution \(3_1\) convergence run at 8192, 16384, and 32768 centerline points.
- Added adaptive, per-knot resolution planning to the bifurcation atlas with a conservative default minimum of 32768 points.
- Added length- and scale-aware resolution planning to the knot-scale sweep.
- Added `run_full_campaign.py` with sequential execution, logging, resume, failure manifests, and automatic result ZIP creation.
- Added `START_V041_FULL_CAMPAIGN.bat` and a smaller smoke-check BAT.
- Added campaign environment, command, manifest, summary, log, success-marker, ZIP, and SHA-256 outputs.
- Updated schemas and package version to 0.4.1 while preserving all global-orbit and QSM guards.

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
