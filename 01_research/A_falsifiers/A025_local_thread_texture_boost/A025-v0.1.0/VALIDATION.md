# Validation — v0.1.0

Validation was performed in the generation environment on a synthetic 180-point trefoil centerline.

## Python/reference path

- Python syntax compilation: **PASS** (`python -m compileall`).
- QUICK blind campaign: **PASS** structural status.
- Uniform boost null: `3.50e-16 R_g`.
- Rigid translation covariance: `1.31e-15 R_g`.
- Rigid rotation covariance: `3.83e-16 R_g`.
- Conditional radial response: `1.07e-4 R_g`.
- Conditional director response: `2.03e-4 R_g`.
- Radial amplitude ratio: `1.99999937` for the precommitted expected value `2`.
- Manifest and blinded-case SHA-256 integrity checks: **PASS**.

## Extended convergence path

Resolution ladder `N = 128, 256, 512`: **PASS**.

Relative change of the conditional radial response between `N=256` and `N=512`:

`1.857e-4`, below the configured `0.20` convergence threshold.

## Native C++ status in this generation environment

The C++17/pybind11 source and strict Windows build path are included, but the generation container does not have the `pybind11` Python package/headers installed. Therefore a native binary was **not** compiled here. `run_all.cmd` intentionally performs a strict native build and then `run_selftest.py --require-native` on the user's Windows environment before any BASIC campaign.

This is not recorded as a native PASS.
