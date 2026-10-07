# VALIDATION — A056 v0.1.0

Validation was executed in the ChatGPT build environment with the `full` profile on the self-contained synthetic control campaign.

## Results

- Python numerical self-test: **PASS**.
- Mittag-Leffler exponential-limit check: max absolute error `1.1102230246251565e-16`.
- Blind sentinel scan: **PASS**.
- G0 provenance: **PASS**; 5 cases hashed.
- G1 admissibility: **PASS**; 5/5 cases.
- G2 spectral qualification: **PASS**; 5/5 cases.
- G3 Sine-Gordon competition: 3/5 support cases, exactly matching the three preregistered SG positive controls after reveal.
- G4 Mittag-Leffler competition: 3/5 support cases, exactly matching the three preregistered ML positive controls after reveal.
- G5 independent replication: **PASS** for the synthetic campaign.
- G6 joint closure: **PASS** for the two independent synthetic SG+ML positive groups.
- Reveal control check: **IMPLEMENTATION_VALIDATED**, 5/5 classifications correct.

Representative positive-control fits recover the injected dimensionless Sine-Gordon coefficients near unity (`a ≈ 1.0014`, `b ≈ 0.9994`) and Mittag-Leffler parameters near the injected `alpha = 0.72`, `tau = 3`. Negative controls select Klein-Gordon or bi-exponential competitors as intended.

## Native-backend status

The Python reference path was executed here. `pybind11` was not installed in the build container, so the C++17/OpenMP extension was not compiled in this validation environment. `run_00_setup.cmd` installs `pybind11`, builds the native module, and `run_10_selftest.cmd` performs native/Python parity automatically when the module is present.

## Scientific status

These are synthetic implementation controls only. They do not constitute SST/PKLSA evidence. A scientific run requires a preregistered dynamical provider that supplies a qualified phase field `phi(t,s)` and ringdown observable or permits the frozen POD-derived ringdown path.
