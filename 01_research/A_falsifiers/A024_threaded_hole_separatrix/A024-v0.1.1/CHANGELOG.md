# Changelog

## v0.1.1
- Windows UTF-8 hotfix: all Python report/config/seal text reads and writes now use explicit `encoding='utf-8'`.
- `_common.cmd` forces `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` as a second defensive layer.
- Fixes `UnicodeEncodeError` on CP1252 Windows locales when `CONCLUSIONS.md` contains `Δ` or `²`.
- No physics, geometry, blind scoring, thresholds, topology, pressure-Poisson, or campaign parameters changed.

## v0.1.0

- New threaded-hole substrate falsifier separated from Fourier-vs-Ideal source testing.
- Added torus `T(2,3/5/7/9)` stratum.
- Added Fremlin twist-knot `4_1`, `5_2`, `6_1`, `7_2` stratum with geometric thread-axis search.
- Added `T(3,3)` three-unknot-link triple-gear proxy.
- Added closed helical/racetrack thread loops with far return path; no open vorticity lines.
- Added active-vs-zero-circulation null pairs with identical geometry and component count.
- Added self-confinement, restoring-mode, pressure-Poisson, far-profile and circulation-similarity gates.
- Added SHA-256 blind sealing and post-seal reveal.
- Added source qualification that excludes suspect/converted/derived `.fseries` fixtures from the primary twist set.
- Added native C++17/pybind11/OpenMP kernels and Windows one-click CMD workflows.
