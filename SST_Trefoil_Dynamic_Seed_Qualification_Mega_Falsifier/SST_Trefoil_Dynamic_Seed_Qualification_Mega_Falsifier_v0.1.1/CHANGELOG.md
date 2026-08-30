# Changelog

## v0.1.1 — S40→S50 recurrence boundary / gate-leakage hotfix

- Fixes the real BASIC crash when `stage40_long/results.json` contains JSON `null` for a non-finite `best_return` or `best_return_time`.
- Adds a fail-closed S40→S50 eligibility validator: missing/non-finite return values are rejected, never compared numerically.
- Makes S50 inherit the complete S40 eligibility contract, including `completed`, loose-return threshold, positive return time, and `long_max_mesh_ratio`.
- Adds rejection reasons/counts to S40/S50 summaries for auditability.
- Adds regression tests for JSON `null` recurrence values and S40 mesh-gate inheritance.
- No Biot–Savart, integration, rolling-score, candidate-generation, or preregistered threshold changes.

## v0.1.0 — Trefoil dynamic seed qualification mega-chain

- Makes start-shape selection itself a blind falsification stage.
- Generates controlled shape-space variants from actual trefoil source files.
- Adds early rigid-normal rolling decomposition, SE(3)-reduced drift, high-k and POD metrics.
- Adds preregistered blind local refinement around top anonymous early seeds.
- Adds N=64/96/128 resolution qualification.
- Adds core-radius robustness before long-run nomination.
- Adds long-horizon recurrence qualification with recorded tangential mesh redistribution.
- Adds near-RPO plus projected Fourier-normal Floquet monodromy.
- Adds downstream material-core vs fixed-core self-generated delay/phase causal gate.
- Uses C++17/OpenMP pybind11 Biot-Savart kernel with explicit MSVC-safe `py::ssize_t`.
- Provides BASIC, EXTENDED and PRODUCTION one-click Windows chains.
