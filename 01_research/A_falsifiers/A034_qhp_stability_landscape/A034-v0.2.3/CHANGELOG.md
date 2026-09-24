# Changelog

## v0.2.3 — 2026-09-21 (PC03)

- Production-certification dual branch: keep archived `dynamic_qhp` FAIL unchanged.
- Adds `pc03_dual_branch.py` with constrained-energy labels:
  `ENERGETIC_STATIONARY_STABLE|SADDLE`, `ENERGETIC_NONSTATIONARY`,
  `REDUCED_MANIFOLD_BREAKDOWN`, `NUMERICALLY_INDETERMINATE`.
- Weak manifold + nice Hessian never auto-promotes.
- CAMPAIGN certs only from real `g,H,C` payloads (never synthetic).
