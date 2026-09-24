# Changelog

## v0.2.0 — PKLSA trefoil population integration

- Replaces the primary synthetic centerline campaign path with provenance-aware PKLSA `knot_3.1` ingestion.
- Adds strict 48-variant census and signed trefoil-bundle checks.
- Adds generic arbitrary-centerline C++17/pybind11 vorticity-tube initialization.
- Adds closed-arclength resampling, centering and uniform RMS-radius normalization.
- Adds salted anonymous geometry/case IDs; candidate IDs, PTSA IDs and parameter triples remain reveal-only.
- Adds dependency-aware population accounting: 48 PKLSA variants are not treated as 48 independent source confirmations.
- Fixes the multi-seed convergence contract: only replays of the same geometry can satisfy cross-resolution BKM escalation.
- Adds BASIC, smoke and 3-resolution certification configs.
- Adds 6-test regression suite and end-to-end schema-fixture smoke validation.
