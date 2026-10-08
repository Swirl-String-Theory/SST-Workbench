# Changelog

## v0.2.0 — 2026-10-07

- Migrated A016 to SST Falsifier Framework v1.0.6 canonical thin-instance architecture.
- Preserved v0.1.1 H0-H4 thresholds without retuning.
- Added P0-P2 material vorticity-population / volume / flux exact controls.
- Added P3-P6 exterior potentiality, circulation, nonlocal energy, and far-field scaling branches.
- Replaced serial scientific gate logic by a fan-out DAG so an H*/P* FAIL does not suppress sibling measurements.
- Added strict C++17/OpenMP FP64 Biot-Savart certification against Python/NumPy FP64.
- Added HMAC opaque runtime input IDs and framework commitment/reveal packaging.
- Removed legacy bundled virtual environment, compiled Windows extension, caches, and historical outputs from the source release.
