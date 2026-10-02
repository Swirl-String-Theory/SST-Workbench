# Changelog

## v0.3.0 — E010 / PKLSA v0.3.1 source-native integration

- Replaced the PKLSA-v0.1.1 `families/14_knot_3p1.npz` consumer with the E010-v0.3.1 production trefoil evidence graph.
- Added fail-closed E010 release and `3_1` POC consistency checks.
- Added original-source-byte resolution with Workbench-root relocation support.
- Added raw SHA-256 and exact E010 `PKLSA-GEOMETRY-SHA256-v1` verification before Euler initialization.
- Added default G1/G2/G3 literature-hard-gate exclusion.
- Added mirror/raw/geometry-duplicate exclusion using E010's source-independence ledger.
- Added anonymous independence-group stratification to BLIND outputs without allowing cross-geometry convergence pooling.
- Added `e010_v031_smoke`, `e010_v031_basic`, and `e010_v031_certification_template` configs.
- Retained v0.2.1 Windows/MSVC `py::ssize_t` portability fix.

## v0.2.1 — Windows/MSVC portability hotfix

- Replaced unqualified `ssize_t` in `cpp/native.cpp` with `py::ssize_t`.
- Corrected release/catalog labeling to A047.

## v0.2.0 — historical PKLSA v0.1.1 integration

- Added provenance-aware 48-member PTSA/PKLSA trefoil population ingestion.
## Packaging hotfix — 2026-09-29

- Fixed Windows archive creation when `Path.cwd()` is absolute but the default output directory is relative.
- Archive member names are now computed relative to the resolved output parent, not `root.parent`.
- Added `tests/test_archive_paths.py` to reproduce the original Windows path-shape failure.
- Added `pack_existing_outputs.cmd` / `tools_pack_existing_outputs.py` so a completed campaign can be archived without rerunning the Euler solver.
- No PDE, PKLSA selection, blindness, numerical thresholds, or scientific verdict logic changed.

