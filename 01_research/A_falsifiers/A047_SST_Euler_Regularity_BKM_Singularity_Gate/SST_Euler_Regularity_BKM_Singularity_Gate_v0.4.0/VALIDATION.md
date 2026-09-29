# Validation — A047 v0.4.0

## Parent evidence used to validate the selector

The supplied v0.3.0 combined output archive was extracted and its BLIND selector input checked. The parent contains 116 geometries in 5 anonymous independence groups. The v0.4.0 default selector deterministically returns 8 anonymous follow-up geometries: five mandatory group representatives plus three anomaly slots. Its frozen selection SHA-256 for that uploaded parent result is recorded in `data/A047_v0.3.0_PARENT_BLIND_SELECTION_SNAPSHOT.json`.

The selector module does not open the reveal map. Reveal mapping is a separate function called only after the frozen blind selection has been written and reloaded from disk.

## Package regression suite

Source-only validation in this build environment:

- `pytest`: **16 passed**.
- Tests cover E010 admission, mirror/duplicate exclusion, source relocation, exact E010 geometry hashing, centerline canonicalization, no cross-geometry convergence pooling, parent-blind selection determinism, seed/core resolution diagnostics, spatial and temporal convergence estimators, finite-time model competition, relative-vorticity decomposition, spectral projection/ABC regression, Windows `py::ssize_t`, and archive path handling.

This container does not have pybind11 installed, so the C++ extension was not rebuilt here. v0.4.0 retains the already validated v0.3.0 C++ kernel except for its module-doc version string. `run_00_setup.cmd` builds the extension before tests on the user's Windows environment.

## Source-only Euler smoke

A synthetic smooth trefoil was evolved with the Python fallback seed kernel at `N=12`, `dt=0.001`, `T=0.006`. The run was numerically valid with energy relative drift about `5.6e-15`, divergence RMS about `8.5e-17`, and vorticity growth about `1.021`. This is software validation only.

A separate short mechanism smoke exercised the pressure-Hessian/Lagrangian path. It reproduced the local `M=S-(1/2)epsilon.omega` identity at about `2.7e-16` relative error and kept `|det F-1|` below `4.3e-7` over the tiny test window. The sample-time `F_tt + H F` residual is intentionally diagnostic-only because the current tracker differentiates sampled `F` at lower order.

## Scientific execution boundary

No v0.4.0 scientific spatial/temporal/high-resolution campaign is executed in this package-build environment because the selected carriers reference original source bytes in the user's SST-Workbench. The local run is authoritative.

A critical possible outcome is that S10 blocks later certification because the existing Gaussian core cannot simultaneously satisfy grid-resolution and slender-core requirements at practical `N`. That is a scientific/numerical finding, not a software failure.
