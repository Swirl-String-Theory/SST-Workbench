# Changelog

## v0.2.1 — acceptance gates

- Fixed nonlocal self-contact: exclusion is now an arclength window in units of \(D\) (default \(2D\)), not a 4% index-fraction gap that measured local chords.
- Added an exact non-local minimum fallback when the kNN self-scan saturates inside the exclusion window.
- Replaced recursive contact-graph union-find with iterative path compression (avoids `RecursionError` on large contact sets).
- Curvature/torsion high quantiles are now arclength-weighted; `standard_ropelength_radius` divides by the declared diameter.
- Added \(n^4\)-weighted `curvature_spectral_tail_fraction` and arclength fraction over the \(\kappa D>2\) bound.
- Added `thickness_gate` (curvature / self / mutual admissibility of declared \(D\)) and `curvature_mode_convergence` ladder.
- Summary features now include `thickness_gate_passes`, `allowed_diameter_D`, `binding_constraint`, `curvature_spectral_tail`, `largest_converged_cutoff`.

## v0.2.0 — native production upgrade

- Replaced the production Biot–Savart path with C++17/pybind11 kernels.
- Added batched evaluation of all circulation-sign sectors.
- Added optional OpenMP parallelization with a configurable thread cap.
- Added strict `--require-native`, `--force-python`, `--force-build`, `--skip-build` and verbose-build controls.
- Added source-hash-based native rebuilds and backend-stamped result signatures.
- Added C++/NumPy parity gates for velocity, Gauss linking and Neumann coupling matrices.
- Added native benchmark and standalone parity-audit runners.
- Added Neumann self/mutual energy decomposition, pair-helicity proxy and global-circulation-reversal checks.
- Added stale-result detection for resumable campaigns.
- Validated all 18 preregistered links in a strict-native quick campaign.

## v0.1.0 — initial prototype

- NumPy implementation of geometry, topology, contacts and regularized Biot–Savart diagnostics.
