# Changelog

## v0.4.0 — Resolution-certified Lagrangian vortex-stretching & BKM mechanism gate

- Added parent-blind follow-up selection from the completed v0.3.0 population screen.
- Selection is frozen and SHA-256 hashed before the v0.3.0 reveal map is read.
- Added S10 seed/core admissibility diagnostics: cells/core, `3 sigma kappa_max`, periodic clearance, spectral-tail fraction, and estimated required resolution.
- Added explicit same-geometry S20 spatial convergence and S22 temporal convergence gates.
- Added long-window S30 Euler continuation for upstream survivors.
- Added S40 Lagrangian material tracer and deformation-gradient diagnostics: `det F`, Cauchy vorticity relation, integrated strain-alignment closure, velocity-gradient/vorticity decomposition, and pressure-Hessian handoff.
- Added S50 finite-time power-law versus nonsingular model competition using AICc and trailing-window stability.
- Added optional S60 core/resampling robustness sweep.
- Added verdict taxonomy that never emits `EULER_REGULARITY_PASS`.
- Preserved E010-v0.3.1 source-native hashes, blindness, Windows/MSVC portability, archive-path hotfix, and same-geometry-only replication.
- Added a source-only Python fallback for the seed kernel so protocol tests can run without a compiled extension; production setup still builds and uses the C++/pybind11 kernel.

## v0.3.0 — E010 / PKLSA v0.3.1 source-native integration

- Replaced PKLSA-v0.1.1 NPZ ingestion with the E010-v0.3.1 source-native trefoil evidence graph.
- Added fail-closed E010 release/source/hash checks and anonymous independence-group stratification.
- Added Windows archive-path packaging hotfix.

## v0.2.1 — Windows/MSVC portability hotfix

- Replaced unqualified `ssize_t` with `py::ssize_t` and aligned catalog identity to A047.
