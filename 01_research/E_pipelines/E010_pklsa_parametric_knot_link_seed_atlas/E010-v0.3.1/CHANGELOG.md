# Changelog

## v0.3.1 — 2026-09-25

Literature-gate release derived from E010/PKLSA v0.3.0.

### Added

- `G1_isotopy_safe_sampling`: Li--Peters finite numerical isotopy-safety proxy.
- `G2_writhe_quadratic_convergence`: Cantarella-inspired writhe-order gate.
- `G3_signed_frenet_chirality_completeness`: preserves signed torsion and signed writhe per Liu et al. (2026).
- `B1_ideal_trefoil_ropelength`: contextual Przybyl--Pierański benchmark with upstream-reference audit separated from recomputed reach.
- `B2_torus_analytic_geometry`: Oberti--Ricca torus-knot analytic controls.
- `D1_hasimoto_phase_holonomy`: signed torsion phase diagnostic.
- `D2_vortex_dynamics_handoff`: geometry-readiness diagnostic for later finite-core/Biot--Savart work.
- Regression tests and machine-readable `VALIDATION_V031.json`.
- `docs/LITERATURE_GATES_V031.md` with equations, assumptions, limits, and citations.

### Changed

- Replaced midpoint Gauss quadrature for `Wr`, `ACN`, and linking number with exact polygonal segment-pair solid-angle integration.
- Added identical exact kernels to the C++/OpenMP backend.
- Publication config enables `literature_gate_mode = enforce` for the three hard geometry-integrity gates.
- Qualification records signed torsion integral, subcurve total-curvature estimate, torsion-sign diagnostics, and Hasimoto phase modulo \(2\pi\).
- Release schema bumped to `PKLSA-HIGH-RES-QUALIFICATION-3`.

### Known open gate

The bundled Gilbert ideal trefoil passes all hard v0.3.1 gates, but the recomputed `reach/dcsd` ropelength is about 7.32% above the high-resolution ideal-trefoil benchmark. `B1` is therefore soft by default pending a dedicated thickness/contact-set certification upgrade.
