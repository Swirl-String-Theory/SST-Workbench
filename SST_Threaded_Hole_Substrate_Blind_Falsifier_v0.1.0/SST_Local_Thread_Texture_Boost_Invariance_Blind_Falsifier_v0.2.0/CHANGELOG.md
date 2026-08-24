# Changelog

## v0.2.1 — Windows/setuptools native-build hotfix

- Fixes `Multiple top-level packages discovered in a flat-layout` with setuptools 80+ / 84 on Windows.
- Generated native `setup()` now explicitly declares `sst_thread_falsifier` and `sst_thread_falsifier.native_ext`; `cpp/` and `config/` are no longer candidates for package auto-discovery.
- `pyproject.toml` also declares the same package list as a second guard against setuptools flat-layout discovery.
- Adds a dependency-preflight regression guard for the explicit package declaration.
- No change to the v0.2 closed-thread physics, blind gates, fixed-core model, RK2 evolution, or thresholds.

## v0.2.0 — explicit closed-thread physics upgrade

- Replaced v0.1.0 radial potential-flow and affine-strain proxies with explicit closed vortex filaments.
- Added local large-source-radius bundle approximation appropriate to Earth-/Sun-like source directions.
- Added remote return-flux closures and G5 near/mid/far locality convergence.
- Added multi-step midpoint RK2 evolution with knot self-induced velocity recomputed every substep.
- Added primary + secondary nonparallel bundle case.
- Added circulation-weight thread-density gradient case.
- Added shared hidden orientation set across every topology.
- Added fixed core radii based on a resolution-independent reference \(R_g\).
- Added G10 resolution convergence classification.
- Added C++17 `filament_velocity` and full `evolve_frozen_background` kernels.
- Retained pure-Python reference implementation and strict native-vs-Python selftest.
- Added `run_all_highres.cmd` and `config/highres.json`.
- Kept bridge claims epistemically separate from structural/covariance claims.
