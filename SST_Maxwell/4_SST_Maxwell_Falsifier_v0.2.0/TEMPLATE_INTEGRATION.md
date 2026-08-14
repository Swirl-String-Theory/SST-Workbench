# Integration of `SST_cpp_pybind_audit_template`

The supplied C++/pybind audit template pattern is retained structurally rather than copied as an inert example.

| Template role | v0.2.0 implementation |
|---|---|
| lazy native import with Python fallback | `native_ext/core.py` |
| build-if-needed + source hash/stamp | `native_ext/build_ext_if_needed.py` |
| C++ source isolated from Python audit layer | `cpp/native.cpp` |
| strict native preflight | `run_native_preflight.cmd` |
| automatic build during install | `run_install.cmd` |
| Python fallback when native is unavailable | `maxwell_sst/kernels.py` |

The example `add(a,b)` kernel from the template has been replaced by the computationally dominant SST kernels:

1. regularized Biot--Savart evaluation;
2. Gauss linking integral;
3. regularized filament energy;
4. midpoint writhe integral.

The C++ implementation releases the Python GIL around the heavy loops and attempts OpenMP parallelization. The build system first tries OpenMP and automatically retries as optimized serial C++ if the platform's compiler rejects the OpenMP flags.
