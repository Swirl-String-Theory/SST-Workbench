# Changelog

## v0.5.1 — Global Fermat Geodesic Shooting and Monodromy

- Added the full three-dimensional ray equation for the conformal Fermat metric `g_F=S^-2 delta`.
- Added RK4 ray integration with real-clock-domain termination, optical-length accumulation, and tangent normalization diagnostics.
- Added five-variable damped Gauss--Newton closed-orbit shooting from local radial-minimum seeds.
- Added integration-step convergence and a second centerline-resolution convergence gate.
- Added a reduced four-dimensional finite-difference monodromy map with eigenvalue and reciprocal-pair diagnostics.
- Added perturbation-scale convergence for monodromy; certification requires a globally certified orbit.
- Added `run_geodesic_shooting.py`, `run_orbit_convergence.py`, `run_monodromy.py`, and the global campaign runner.
- Added separate smoke and full Windows launchers.
- Preserved `qsm_certified=false`; no complex-frequency wave solver is included.

## v0.4.3 — Threshold Censoring and Clock-Domain Metadata

- Added explicit connected real-clock component metadata and clock-boundary brackets.
- Corrected valid-ray versus fully-valid-ray semantics.
- Replaced ambiguous threshold labels with censoring and present/absent brackets.

## v0.4.2 — Clock-Domain Root-Refinement Hotfix

- Rejected clock-invalid bisection intervals and prevented complex clock-domain arithmetic.

## v0.4.1 — Campaign Automation and Certification Corrections

- Added adaptive campaign, convergence, scale, logging, resume, and ZIP automation.

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
