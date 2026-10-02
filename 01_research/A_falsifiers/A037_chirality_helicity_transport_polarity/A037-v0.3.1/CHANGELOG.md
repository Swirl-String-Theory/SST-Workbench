# Changelog

## v0.2.0 — 2026-08-28

- Replaced flattened one-curve representation with true multi-component closed-filament geometry and explicit offsets.
- Added VECT component parsing, blank-block parsing, gap-based component splitting and guarded torus `gcd(p,q)` recovery.
- Generic ambiguous link files are rejected instead of connected by artificial segments.
- Added native multi-component finite-core Biot–Savart superposition.
- Added operator-consistent centerline helicity `Xi_H^CL` and multi-component Gauss helicity/linking diagnostic.
- Added explicit relative-equilibrium fit `F ~= U + Omega x X`; no physical PASS is possible above the configured residual gate.
- Replaced frozen-J primary dynamics with matrix-free trajectory variational evolution `dX/dt=F(X)`, `d(deltaX)/dt=DF[X(t)]deltaX`.
- Added central-difference Jacobian-vector products, exact reuse of the base RK4 stage states by the tangent RK4 update, and trajectory CFL/mesh/length/shape gates.
- Added rigid-mode subtraction and tangential/gauge contamination diagnostics.
- Replaced the grid-sensitive hard split as primary response by a smooth periodic odd directional-energy moment; retained the hard split only as a diagnostic, alongside centroid drift, Fourier polarity and independent amplification growth.
- Added local differential chirality texture and launch-point response correlation.
- Added excitation-by-excitation mirror matching `s_0 <-> (-s_0) mod 1`, so aggregate cancellation cannot hide a local parity defect.
- Pair statistics now use one mirror pair as one independent observation; added label-invariant `beta` diagnostic.
- Added `PASS_SINGLE_COMPONENT_*` versus `PASS_MULTICOMPONENT_*` distinction.
- Moved private reveal mapping outside the blind output tree; automatic BLIND ZIP no longer contains the mapping.
- Reveal now verifies seal + commitment before copying `REVEAL_MAPPING.json` into the revealed output.
- Added automatic `run_35_archive_blind.cmd` and `run_45_archive_revealed.cmd` to prevent the v0.1 archive/reveal mix-up.
- Added targeted BASIC priorities for trefoil `3_1`, `7_4`, `4_1`, `T(2,7)` and multi-component controls when available.
- Added a separate low-resolution frozen spectral diagnostic; explicitly not labeled true Floquet monodromy.

## v0.1.0 — 2026-08-28

- Initial blind original/parity-mirror A/B protocol.
- Single flattened filament representation.
- Frozen transverse Jacobian dynamics.
- Helicity/writhe and Fourier-polarity mirror gates.
