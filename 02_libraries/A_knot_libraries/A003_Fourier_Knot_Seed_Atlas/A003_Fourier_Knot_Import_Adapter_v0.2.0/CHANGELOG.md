# Changelog

## v0.2.1 — CLI/CMD compatibility hotfix (2026-10-19)

- Fixed `run_all.cmd`: use supported `--reference-core-radius-units` rather than incompatible `--a-star`.
- Added `--a-star` as deprecated parser alias for backwards compatibility with an alternate v0.2.0 script.
- Added `run_g5.cmd`, using the correct v0.2.1 G5 switches; G5 remains opt-in.
- `SST_A003_REFERENCE_CORE_RADIUS_UNITS`, legacy `SST_A003_A_STAR`, and optional `SST_A003_RUN_G5` now work in CMD.
- Added Windows script/CLI contract regression tests. All scientific gates and source atlas hashes remain unchanged.


## v0.2.0 — G4 scale contract and G5 independent invariant screen (2026-10-19)

- Kept A003 v0.1.1 atlas pin `a205fb8a2747d1b23bcb8c0242c64e8b136a5e961becf8befda9c52d8d328b82` and all G0–G3 tolerances.
- Added `--reference-core-radius-units` to convert every source polygon's *measured* dimensionless length into SI units, conditional on explicit `a*`. Canonical `r_c` is preserved.
- Added optional independent `pyknotid` Alexander determinant comparisons for the 30 seed geometries; BASIC/FULL/ALL choices, rechecks source file SHA-256 at the point of G5 use.
- Preserved `UNVERIFIED` / `NOT_REGISTERED` knot status and unverified chirality even when determinants agree, because Alexander determinant is not complete.
- Added G5 fail-closed behavior for mismatches, unavailable provider and unresolved provider errors; audit reports are saved before exit 2.
- Updated `run_all.cmd` to support optional environment variables without changing the old no-arguments path behavior.
- Added 8 focused G4/G5 regression tests (19 tests total), retaining the legacy 11-test suite and no unreviewed threshold changes.
- No source XYZ modifications, no canonical index changes, and no physics/PKLSA promotion.

## v0.1.1 (frozen baseline)

- Sibling A003 atlas path detection and non-silent explicit overrides.
- Full 240 XYZ hash/schema audit, geometric mirror diagnostic and sampling convergence.
