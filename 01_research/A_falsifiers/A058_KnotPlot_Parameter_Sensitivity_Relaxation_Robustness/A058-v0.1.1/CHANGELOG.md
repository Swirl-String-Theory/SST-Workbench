# Changelog

## v0.1.1
- Adopt user-supplied KnotPlot shortcut target as an automatic runtime default.
- Support both `%USER_PROFILE%` and standard Windows `%USERPROFILE%`.
- Adopt `%SST_WORKBENCH%\04_tools\A_geometry\A001_knotplot\` as preferred Start-In.
- Allow `outputs` as an explicit Start-In selector and output-directory fallback when A001 is unavailable.
- Generate absolute campaign result paths so Start-In cannot redirect scientific outputs.
- Record executable SHA-256 and resolved Start-In in `campaign/runtime_<tier>.json`.
- Remove pre-generated target-machine campaign scripts/manifests from the release; regenerate them locally before FREEZE.

## v0.1.0 — 2026-10-07
- First Framework-v1.0.6 parameter-sensitivity falsifier for the historical KnotPlot export pipeline.
- Imports all 50 uploaded knot/link/torus build scripts unchanged.
- Adds explicit save-format provenance audit.
- Adds smoke/pilot/full campaign generator, atomic KnotPlot batch runner, checkpoint metric capture, null-control design, force ablation, numerical sweeps, relaxation plateau and resolution tests.
- Adds optional strict C++/pybind11 FP64 metric certification.
- Gates continue diagnostically after prior scientific FAIL states; only G0 integrity is foundational.
