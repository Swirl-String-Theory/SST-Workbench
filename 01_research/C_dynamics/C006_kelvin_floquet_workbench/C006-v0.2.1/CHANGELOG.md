# Changelog

## v0.2.1 — 2026-09-13

- Instrumentation-only copy-on-write from v0.2.0. No K0–K14 science, no Floquet unlock.
- Adds preregistered Biot–Savart tube-field bridge \(P_{\rm BS}\) with biorthogonal \(p_m^\dagger W_r B\) amplitude.
- Adds mode-reconstruction, tube-validity, and bridge-qualification certificates.
- Does not feed A029-v0.4.0 M0–M3. Qualification and scoring sets stay disjoint.
- `BRIDGE_REJECTED` does not falsify the A029 modal clock.

## v0.1.1 — 2026-08-10

- Fixed Windows MinGW/Strawberry direct linking: the builder now emits exactly one resolvable CPython import-library name instead of requiring both `pythonXY` and `pythonX.Y`.
- Fixed the setuptools fallback on setuptools 80+ by explicitly declaring `sst_kelvin_workbench` rather than invoking flat-layout auto-discovery.
- Added `[tool.setuptools] packages = ["sst_kelvin_workbench"]` to `pyproject.toml` for the same explicit-package policy.
- Added regression tests for the Windows link-name selection and generated setuptools fallback script.
- No scientific K0--K14 equations, thresholds, reference results, or alpha-blind gate logic changed.

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
