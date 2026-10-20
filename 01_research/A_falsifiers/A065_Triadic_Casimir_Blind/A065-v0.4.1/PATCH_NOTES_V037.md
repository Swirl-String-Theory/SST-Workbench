# v0.3.7 Finite-Core Inference Research Falsifier

- Added precommitted analytic Gaussian/Rankine finite-vorticity cross sections with circulation, enstrophy and held-out radial observables (not measured PKLSA).
- Profile-specific inverse a(Gamma,Z) computed with **no** fit to held-out radial velocity/pressure. The profile-independent epsilon hypothesis (single Rosenhead kernel) fails held-out controls; this negative result is retained as G24 FAIL.
- New G22–G27 are additive; physical PKLSA source gate G27 UNRESOLVED; cannot upgrade G3/G8 physical status.
- Optional native C++17 radial evaluation verifies Python only at kernel level.
- Dedicated run: `run_all.cmd CORE`, output `outputs/FINITE_CORE_V037_RESULT.json`, `reports/FINITE_CORE_V037_REPORT.pdf` and editable `.tex`.
- Full official FRAMEWORK/ALL requires **unchanged external canonical framework v1.0.7**. Never vendor or modify frozen runtime.
- All 11 protected data/seal files are inherited unmodified from v0.3.6.
