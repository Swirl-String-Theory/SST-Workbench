# Validation — v0.1.0

## Executed in the artifact environment

- Python regression suite: **8/8 PASS**.
- Python `compileall`: **PASS**.
- MSVC portability scan: **PASS** — no unqualified POSIX `ssize_t`; native code uses `py::ssize_t`.
- Blind prepare → blind dynamics → SHA-256 seal → reveal smoke chain: **PASS**.
- Pressure-Poisson smoke route: **PASS** with finite pressure deficit and both far-profile fits.
- Extended preregistration preparation: **9/9 carrier geometries PASS** source/hole/thread qualification.
- Public blind pair table contains no carrier IDs, family labels, `active`, `null`, beta, source, or link matrix: **PASS**.

## Geometry/topology checks

- `T(2,3/5/7/9)` central closed probe-thread: nonzero Gauss linking, approximately 2 at validation resolution.
- Fremlin `4_1`, `5_2`, `6_1`, `7_2`: geometric axis search finds finite-clearance nonzero-linked central passages.
- `TRIPLE_GEAR_T3_3`: 3 components; pairwise `|Lk| ≈ 1`; central thread links all three components approximately once.
- Thread loops are closed; no vortex endpoint is introduced.

## Native backend

The package contains a C++17/pybind11/OpenMP implementation and turnkey Windows build script. Exact native compilation could **not** be executed in this artifact container because `pybind11` is not installed here and outbound package download is disabled. `run_00_install.cmd` installs `pybind11` before `run_01_build_native.cmd`; extended/family production presets refuse to run without `backend=cpp-pybind11`.

The native source follows the already MSVC-corrected indexing style (`py::ssize_t`) and contains no POSIX `ssize_t` dependency.

## Scientific interpretation guards

- A thread-induced carrier stability improvement does not imply gravity.
- A central pressure deficit does not imply a Newtonian potential.
- The `1/r` and `1/r^2` fits compete blind; a better `1/r^2` result is an explicit negative result for this gravity closure.
- Absolute circulation dependence is checked separately because ideal Euler/Biot-Savart scaling predicts trajectory collapse after nondimensional time rescaling at fixed beta and geometry.
- The triple-gear carrier is a topology/hydrodynamic proxy, not a gear-tooth contact simulation.
