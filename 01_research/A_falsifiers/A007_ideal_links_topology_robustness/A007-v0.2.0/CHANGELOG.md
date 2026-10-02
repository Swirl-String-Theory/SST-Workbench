# Changelog

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
