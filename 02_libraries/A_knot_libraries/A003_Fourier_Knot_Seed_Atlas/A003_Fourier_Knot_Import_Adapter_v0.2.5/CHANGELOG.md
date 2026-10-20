# Changelog

## 0.2.5 (2026-10-19) — Projection-robustness diagnosis (FAIL_CLOSED)

- Frozen F3 v0.2.4 `N=2400, projection 1` actual provider failure as SHA-tracked regression fixture; F4 preserved as positive control.
- Added independent polygon projection diagnostics: crossing count, angle sine, normalized depth gap and numerical near-degeneracy indicators.
- Added two fixed supplementary diagnostic views; the original primary views remain unchanged and alone determine G5 status.
- Reclassified `v3=0` as `UNRESOLVED_ZERO_V3_WITNESS`, never mirror-chirality evidence.
- Maintained G5a mismatch / G5d fail-closed; no automatic promotion even if extra views match.
- Added `replay_g5_v024.py`, `run_g5_replay.cmd`, `run_g5_projection_robustness.cmd`, historical and mock regressions.
- Inherited all v0.2.4 G0–G4, G5c limits and hashed source data. G6 NOT_RUN.

## 0.2.4 — prior release

# A003 Fourier Knot Import Adapter v0.2.4 — Extended G5

Parent: v0.2.3. Atlas dependency: A003-v0.1.2 (byte-frozen).

- Added `g5_extended.py` with independently calculated symbolic Alexander polynomials from polygon coordinates, degree-3 Vassiliev mirror parity, controlled two-projection × two-resolution checks, and fail-closed source SHA-256 verification.
- Added analytical torus polynomial and independent modular unreduced Burau positive braid calculation; G5c algebraic results are explicitly *not independent checks of the XYZ embedding*.
- Added a predeclared crossing complexity limit. High-crossing torus knots and unnamed higher Fibonacci Fourier knots stay `UNRESOLVED`; no implicit promotion to `CERTIFIED` or `CHIRALITY_CERTIFIED`.
- Added CLI options: `--g5-extended`, `--g5-extended-max-crossings`, and `--require-g5-extended-complete`. Kept determinant-only G5 options and behavior.
- Added `run_g5_extended_fibonacci_torus.cmd`, `run_g5_extended_twist.cmd`, `run_g5c_braid_reference.cmd`, and a standalone algebraic report generator.
- Retained v0.2.3 NumPy 2.x temporary compatibility shim, G0–G4 thresholds, all 384 XYZ source hashes and their original scientific statuses.
- Added 11 deterministic extended-G5 regression tests, including negative controls and compatibility with normal Laurent polynomials. G6 remains `NOT_RUN`.
- Actual `pyknotid` enhanced polynomial/v3 provider execution was **not performed in the artifact environment**; the user must run the new G5 CMD programs in the Windows `.venv`.
