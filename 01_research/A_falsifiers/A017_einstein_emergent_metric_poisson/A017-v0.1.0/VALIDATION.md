# Validation status

Validated in the artifact runtime before packaging:

- Python source compilation: PASS.
- Python unit tests: `3 passed, 1 skipped`.
- Python fallback synthetic self-test: PASS.
- Synthetic closed circle: fitted far-tail exponent for `v^2` = `5.90637`.
- Synthetic closed trefoil: fitted far-tail exponent for `v^2` = `5.99631`.
- Pressure-Poisson algebraic identity residual in the synthetic checks is at floating-point roundoff.

The skipped test is the C++/Python parity test because this artifact runtime does not have the `pybind11` build dependency installed and has no package-download network access. The Windows workflow installs `pybind11` from `requirements.txt`, builds the extension, then reruns the parity test before a normal campaign. `run_all*.cmd` aborts if that build/test fails.
