# Validation v0.1.0

Validation performed before packaging:

- Python test suite: **7 passed**.
- C++17 source: syntax-checked with GCC 14.2 against pybind11 headers.
- Native extension: manually compiled on Linux for runtime validation only; the platform-specific binary is **not included** in the ZIP.
- Native/Python parity:
  - finite-core interaction energy relative error: ~`1.35e-16`;
  - Biot-Savart velocity relative error: ~`9.67e-17`;
  - Gauss-linking absolute difference: `0` in the parity control;
  - segment-distance relative difference: `0`;
  - doubly-critical-distance proxy relative difference: `0`.
- Synthetic circular vortex ring: relative-equilibrium normal residual approximately machine precision.
- Deliberately perturbed ring: substantially larger relative-equilibrium residual, confirming control discrimination.
- Meridian-loop holonomy control: converges to integer circulation when the source centerline is sufficiently resampled.
- End-to-end blind campaign + freeze + reveal path was exercised on a representative trefoil text centerline without pipeline errors.

Windows/MSVC compilation is performed locally by `run_00_install.cmd`; the workbench intentionally rebuilds the extension for the user's active Python ABI.
