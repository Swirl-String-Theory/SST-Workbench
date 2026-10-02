# Validation status — v0.1.0

Validation performed during package construction on 2026-08-29.

## Passed

- Python smoke tests: **7/7 passed**.
- Stereographic inverse/project roundtrip error gate passed.
- Uniform arclength resampling gate passed.
- Track-trefoil generation finite/closed-polyline checks passed.
- Bishop material bundle shape checks passed.
- Classic trefoil framed-knot check:
  - midpoint Gauss `Wr ≈ -3.35446`
  - midpoint Gauss `Lk ≈ -3.00018`
  - inferred `Tw = Lk-Wr ≈ +0.35428`
  - integer linking residual `≈ 1.82e-4`.
- Standalone C++17 geometry kernels compiled with `g++ -std=c++17 -O2` and passed a planar-circle self-test (`Wr = 0`).
- Reference resolution ladders generated for classic trefoil, anisotropic track trefoil, standard `T(2,3)`, and S3 figure-eight control.

## Deliberate negative reference

At the demo dimensionless `core_radius = 0.05`, the default S3 figure-eight projection fails the geometry qualification gates because its stereographic embedding has high local curvature / low clearance. This is intentional: S3 transforms are tagged as nonphysical geometric controls and are not automatically accepted as physical seeds.

## Environment limitation

The complete pybind11 extension could not be built inside the construction container because that container did not have `pybind11` installed and had no package-network access. The pure C++ kernel used by the extension was compiled independently. On Windows, `run_all.cmd` installs `pybind11` first and then builds the extension with MSVC `/std:c++17 /O2 /openmp`.
