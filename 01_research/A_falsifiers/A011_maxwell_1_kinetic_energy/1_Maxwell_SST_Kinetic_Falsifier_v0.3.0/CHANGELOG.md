# Changelog

## v0.3.0

- Added Boltzmann 1877 combinatorial complexion/permutability audit.
- Added Boltzmann occupation-law fit with inferred temperature, `R^2`, and KL divergence.
- Added optional detailed-balance equilibrium gate.
- Added accessible-state entropy and microcanonical temperature from `state_counts.csv`.
- Added entropy-gradient force estimator and blind force-reference comparison.
- Added SST pressure-gradient force fallback using canonical `rho_f`.
- Added pressure/temperature integrability gate.
- Added Verlinde entropy-displacement, holographic area-law, inferred-`G`, equipartition, inverse-square, and potential/entropy audits.
- Added canonical `r_c/l_P` hierarchy guard.
- Added explicit `research_claims` so speculative bridge assumptions fail only when preregistered.
- Added complete synthetic PASS and FAIL datasets for all new gates.
- Added `run_all.cmd`, `run_all_boltzmann_verlinde.cmd`, `run_40_bv_demo_pass.cmd`, `run_41_bv_demo_fail.cmd`, and `run_42_bv_physical.cmd`.
- Expanded the physical campaign skeleton with v0.3 statistical-closure CSV schemas.
- Added v0.3 unit tests and source-traceability documentation.

## v0.2.0

- Solver-facing centerline geometry, Kelvin/shape candidate, encounter proxy and C++17 acceleration layer.
