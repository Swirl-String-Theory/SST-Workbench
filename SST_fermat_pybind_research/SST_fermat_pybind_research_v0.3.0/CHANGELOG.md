# Changelog

## v0.3.0

- Added adaptive per-knot centerline resolution using a target `mean(Delta s)/epsilon` ratio.
- Added explicit selected/capped/underresolved resolution-plan classifications.
- Added exact straight-reference Rosenhead horizon and critical softening thresholds.
- Added `run_softening_matrix.py` across `0_1`, `3_1`, `4_1`, and `5_2`.
- Added `full`, `spot`, and `none` native/Python parity modes for softening scans.
- Added `run_resolution_ladder.py` with fixed physical probes across centerline resolutions.
- Added `run_profile_matrix.py` for one-dimensional Rankine, Rosenhead, and Lamb--Oseen comparisons.
- Added ray diagnostics separating interior, lower-boundary, upper-boundary, and invalid minima.
- Added explicit `rosenhead_midpoint` kernel-model metadata to Python and C++ calls.
- Added Rosenhead threshold and adaptive-resolution checks to `run_all_checks.py`.
- Preserved all local-candidate, global-orbit, and QSM epistemic guards.
- No SSTcore dependency or SSTcore source modification.

## v0.2.0

- Added exact uploaded ideal-Fourier centerlines for `0_1`, `3_1`, `4_1`, and `5_2`.
- Added uniform-arclength resampling and centerline source-length validation.
- Added discrete Bishop/parallel-transport normal frames.
- Added four-knot native/Python field parity.
