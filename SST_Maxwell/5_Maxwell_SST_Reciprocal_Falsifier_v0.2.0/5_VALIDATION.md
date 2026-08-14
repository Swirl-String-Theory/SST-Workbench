# 5_Maxwell v0.2.0 validation ledger

Development-time checks performed on the packaged source:

- C++17 pybind11 source compiled successfully in the execution environment using available pybind11 headers.
- `python -m py_compile` passed for all Python sources.
- `tests/run_tests.py` passed all matrix, positive-self-stress, NNLS, force-area, component-split, and native-kernel controls.
- The Canon patch passed `git apply --check` against the supplied `SST_CANON-v0.8.35(2).tex` and `SST_CANON-v0.8.35-research-track(2).tex` after restoring their canonical filenames.
- The shared-final scanner found 41 geometries in the supplied `KnotPlot_relaxed_final.zip`; with the preregistered residual-QC threshold `0.05`, 19 were eligible for equilibrium interpretation and 22 were retained as geometry-QC refusals.
- A 9-case BASIC development smoke campaign completed without runtime errors using the native backend.
- A one-case EXTENDED smoke campaign completed contact-shell sensitivity and near-singular coordinate-perturbation branches.
- On the 300-vertex `knot_3.1_final` contact-kernel benchmark in this environment, the pybind11 C++ kernel was hundreds of times faster than the pure-Python fallback. This benchmark is machine- and compiler-dependent and is not a physics result.

The smoke-campaign PASS/WARN/FAIL values are not bundled as SST evidence. The user-facing CMD runs should regenerate blinded results from the local `..\..\KnotPlot\knots\final` directory.
