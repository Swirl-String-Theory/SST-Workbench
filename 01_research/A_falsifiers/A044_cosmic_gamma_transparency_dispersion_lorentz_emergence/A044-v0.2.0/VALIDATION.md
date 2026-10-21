# Validation record — A044 v0.2.0

Validation performed in the build environment on 2026-10-04.

- Python source import: PASS.
- pytest: **6/6 PASS**.
- Blind campaign execution: PASS.
- Blind-output SST/candidate leakage audit: PASS.
- Conventional Poisson gate: expected count \(\sim10^{-96}\) -> FAIL as intended.
- ALP-only Poisson gate: expected count \(\lesssim10^{-4}\) -> FAIL as intended.
- Generic birefringent linear \(n=1\) primary window: FAIL as intended.
- Published nonlinear \(n=2\) timing scale versus final transparency upper bound: PASS.
- Stable tiny-\(\delta\) numerical evaluation: PASS; direct `1-v_g/c` subtraction is avoided for generated sub-ULP deviations.
- Synthetic target-fitted demonstration candidate: correctly REJECTED by the independent-derivation gate.

The Windows `run_all.cmd` itself was not executed on Windows in this environment. Its Python pipeline was exercised directly; the C++17/pybind11 backend remains optional because the pure-Python reference path is authoritative and was used for this validation.
