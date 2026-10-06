# Changelog

## v0.1.0 — 2026-10-05

- preregisters H0--H3 under one tournament protocol;
- adds dual circulation normalization for two-component links;
- adds target-blind topology-change safeguard;
- imports A051-compatible phase-lock semantics;
- adds model-class admissibility gate separating ideal Euler from finite-core reconnection tests;
- adds Workbench discovery plan for E010/E011/A051/E012;
- separates blind and reveal stages.


## v0.1.0 build hotfix 1 — 2026-10-05

- resolves Windows CMake discovery of pip-installed pybind11 via `python -m pybind11 --cmakedir`;
- removes the hard-coded pybind11 site-packages path;
- makes the native build fail-fast on pip/configure/build errors;
- uses the package-local CMake and Ninja executables explicitly;
- enables modern CMake `FindPython` / `Development.Module` discovery;
- adds a guarded native-parity runner and Windows build diagnostics.

## v0.1.0 buildfix2
- Diagnose and stage MinGW/Strawberry runtime DLL dependencies for the pybind11 extension.
- Explicit Windows DLL search directories for native parity import.
- Prefer static `libgcc`/`libstdc++` linkage under MinGW.
- Print PE import dependencies through toolchain `objdump` when available.
