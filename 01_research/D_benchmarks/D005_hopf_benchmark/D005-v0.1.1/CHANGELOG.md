# Changelog

## v0.1.1

- Fixed pybind11 3.x/MSVC `py::array_t` multidimensional shape construction.
- Replaced mixed brace-init shapes with explicit `std::vector<py::ssize_t>` containers.
- Flattened 3-D OpenMP loops; avoids MSVC C4849 `collapse` being ignored.
- Windows builder now prefers setuptools/MSVC before Strawberry/MinGW `c++`.
- Native backend reports version `0.1.1`.
- No change to H0-H10 formulas, tolerances, or Python reference semantics.

## v0.1.0

- Ported the eight SST Hopf benchmark scripts into the user's C++/pybind audit-template architecture.
- Added C++17 native kernels for the expensive local-grid and O(N^2) geometric operations.
- Added optional OpenMP compilation with automatic non-OpenMP fallback.
- Retained the original NumPy reference path for reproducibility and falsification.
- Added native/Python parity checks.
- Added quick, standard and high-resolution chained runners.
- Added one-click Windows `.cmd` entry points and eight per-step `.cmd` runners.
- Preserved the H0–H10 evidence semantics; open research gates remain open.
- Added `RUN_FULL_VALIDATION.cmd` and `RUN_FULL_VALIDATION_HIGHRES.cmd` for one-click workstation validation.
- Made every per-step `.cmd` self-contained: it repairs the venv when needed, enforces a native backend, runs prerequisites, and propagates failure codes.
