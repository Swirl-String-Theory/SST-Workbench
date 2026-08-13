# Changelog

## v0.1.0 — 2026-08-10

- Created four-phase Kelvin/Floquet workbench K0–K14.
- Added full Rankine-vortex dispersion residual/root benchmark and Kelvin long-wave asymptotics.
- Added canonical SST dimensionless scale diagnostics.
- Extended the existing C++17/pybind11 regularized Biot–Savart kernel with Kelvin benchmark functions.
- Preserved pure-Python fallback and C++/Python parity gate.
- Added weak-amplitude ring mode sweep and ring finite-difference mode spectrum.
- Added bundled `3:1:1` trefoil frozen Kelvin spectrum.
- Reused the strict RPO gate: no accepted RPO means no true Floquet monodromy.
- Added blind 4-wave/6-wave resonance enumeration, sextet time evolution, combination phase, pentacoherence and 4-wave comparison.
- Added finite-time broadband transfer, cumulative flux proxy and linear/nonlinear timescale diagnostics.
- Added four-configuration mirror/circulation chirality audit.
- Added target-blind source scan.
- Added `run_all.cmd` plus phase-specific Windows launchers.
- Added pytest regression tests and fallback quick reference archive.
