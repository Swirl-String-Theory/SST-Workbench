# A054-v0.6.0 validation

Package-level validation before release:

- Python compile: PASS.
- Pytest: **13 passed**.
- Constrained-objective identity test: PASS (`U_c(q)` equals the energy of the exact projected geometry returned by the objective projector).
- Explicit numerical-status tests: PASS (`UNRESOLVED_NUMERICAL` is not converted into provider FAIL evidence).
- Hessian finite-difference sweep presence/sign-authority tests: PASS.
- Implementation commitment recomputation: PASS, exact match.
- Pure C++17/OpenMP energy-core compile: PASS.
- Pure C++ energy-core selftest: PASS (`4.93411`).
- pybind11 3.x source compatibility test: PASS (`py::ssize_t`, `ArrayF64C::ensure`, module declaration).
- Local assistant-container pybind extension build/parity: NOT RUN because pybind11 is not installed in the container and network installation is unavailable.

The Windows installation script remains fail-closed: `run_00_install.cmd` installs the declared requirements, builds `a054_native`, runs pytest, and verifies the implementation commitment before a scientific run can proceed.

Scientific source-native E013/E011 execution is not simulated as evidence during packaging. The actual run must receive `%SST_CROSS_CARRIER_MANIFEST%` from E013 and reload the exact E011-selected source bytes through E010.
