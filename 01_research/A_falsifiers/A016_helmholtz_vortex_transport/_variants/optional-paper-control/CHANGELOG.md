# Changelog

## v0.1.1 — MSVC/Python 3.14 build hotfix

- Fixed Windows/MSVC compilation failure caused by POSIX-only global `ssize_t`; native code now uses `py::ssize_t`.
- Fixed the pybind11 NumPy output-shape casts in `biot_savart` for MSVC.
- Made `native_ext` exports lazy, removing the `runpy` warning when invoking `python -m native_ext.build_ext_if_needed`.
- Improved the install failure message so an existing `cl.exe` is not misdiagnosed as missing Visual Studio Build Tools.
- **Scientific preregistration, thresholds, blind salt, and v0.1.0 config files are unchanged.** This is a software portability hotfix only.

## 0.1.0 — 2026-08-14
- Initial Helmholtz-SST relaxed-knot workbench.
- C++17/pybind11 native Biot-Savart, finite-core energy, Gauss linking and segment-distance kernels.
- Blind identity hashing and post-freeze reveal.
- H0 geometry, H1 convergence, H2 holonomy, H3 relative-equilibrium, H4 symmetry gates.
- Explicit rho_f torsion-sector separation and static-data guard.
- Windows run_all_basic / normal / extended one-click workflows.
