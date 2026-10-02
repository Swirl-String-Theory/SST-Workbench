# v0.2.0 implementation self-test

The distributable package contains no real blind result files.

Validation performed during packaging:

- Python source compilation: PASS.
- Pure-NumPy kernel oddness under \(\Gamma\to-\Gamma\): PASS.
- C++/Python equality harness is included in `run_06_native_selftest.cmd`; the packaging runtime did not contain pybind11 headers, so native compilation was not possible here.
- Basic and extended campaign control-flow was exercised against a temporary copy of the supplied KnotPlot directory using the Python reference backend. Numerical blind observables are intentionally not embedded in this package.
- Blind output freeze/verification logic: PASS.

On the target Windows workstation, `run_00_install.cmd` performs the decisive native C++/OpenMP build and then runs the C++ vs Python equality self-test.
