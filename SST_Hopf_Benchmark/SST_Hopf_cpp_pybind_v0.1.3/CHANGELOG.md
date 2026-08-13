# Changelog

## v0.1.3

- Added fourth-order C++/Python director-curvature kernel.
- Added explicit FFT Hodge projection and longitudinal residual.
- Added STANDARD_PASS / CERTIFIED_PASS qualifications for H1/H3.
- Split H3 linking residuals into integer/spinor/director comparisons.
- Replaced the pseudo seam check with exact branch-cut gauge/director tests.
- Added H5 identity-vs-independent-SST bridge classification.
- Added runtime/backend provenance to patched evidence.
- Added `RUN_DIRECTOR_CONVERGENCE.cmd` and `RUN_HIGHRES_HOPF.cmd`.
- Kept `setuptools>=68` and `wheel>=0.43` as explicit requirements.


## v0.1.2

- `setuptools>=68` restored as an explicit requirement.
- `wheel>=0.43` added as an explicit native-build requirement.
- `cmd/00_SETUP_VENV.cmd` now upgrades `pip setuptools wheel` before installing project requirements.
- Setup performs an explicit import/version preflight for NumPy, pybind11, setuptools and wheel.
- `_ENSURE_NATIVE.cmd` now treats missing setuptools/wheel as an incomplete environment and repairs the venv automatically.

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
