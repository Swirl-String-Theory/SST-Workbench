# Changelog

## v0.3.3 — 2026-09-21 (PC02)

- Production-certification: qualification-before-χ_ij.
- Adds `pc02_qualification.py`: temporal/spatial/mesh ladders must PASS before χ_ij.
- Splits `DISCRETE_OPERATOR_MIRROR_COVARIANCE` (may PASS on bad traj) vs
  `PHYSICAL_TRAJECTORY_SYMMETRY_RESPONSE` (`INVALID_NUMERICS` when under-resolved).
- Label when unqualified: `INVALID_NUMERICS / NOT_YET_TESTED_2505`.
- No new physics observables beyond certificate semantics.
