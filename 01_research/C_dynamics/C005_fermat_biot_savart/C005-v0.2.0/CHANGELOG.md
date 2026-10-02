# Changelog

## v0.2.0

- Added exact uploaded ideal-Fourier centerlines for `0_1`, `3_1`, `4_1`, and `5_2`.
- Added uniform-arclength resampling and centerline source-length validation.
- Added discrete Bishop/parallel-transport normal frames.
- Generalized the local Fermat scan from generated torus knots to catalog knots.
- Added `run_knot_matrix.py` with smoke, standard, and high presets.
- Added native/Python parity checks for every probe vector on all four knots.
- Updated `run_all_checks.py` to avoid false native certification when only the Python fallback is available.
- Retained generated `T(p,q)` scans for backward comparison.
- No SSTcore dependency or SSTcore source modification.
