# v0.3.0 implementation validation

Validation performed in the artifact runtime before packaging:

- Python syntax/compile check: PASS.
- Pure-Python test suite: **6 passed**.
- Exact polygonal solid-angle Hopf-link reference: PASS, `|Lk|=1` within numerical tolerance.
- Independent Biot--Savart circulation against the Hopf target: PASS.
- Mutual-helicity identity against `2*Lk`: PASS.
- Minimal synthetic E010/PKLSA source-native fixture: carrier discovery, raw SHA verification, PKLSA geometry SHA verification: PASS.
- Synthetic end-to-end blind `basic` campaign: PASS; M6 PASS; PKLSA stress anchor PASS; output freeze created.
- Freeze verification + committed unblind key: PASS.
- On the synthetic circular reference, M6 fitted dimensionless slope was approximately `1.0000518`, with `R^2=1` and a null-loop circulation consistent with zero. This is a software/numerical reference test, **not SST evidence**.

## Native build status in this environment

The C++ source and Windows build pipeline are included, but the hosted artifact runtime did not contain the `pybind11` Python package/headers, so the native extension could not be compiled here. The provided `run_00_install.cmd` installs pybind11, installs/builds the local E010-v0.3.x package in the same venv (for E010's exact-linking extension), builds the separate Maxwell-3 C++/OpenMP extension, and then runs the native self-test.

## Upstream Drive inspection

The package was designed against the E010 `v0.3.1` source tree and production metadata found in the user's SST-Workbench Google Drive clone. The inspected release reports the source/native identity gates as available/green while the aggregate `full_campaign_gate_pass` and `publication_ready_geometry_layer` are false. v0.3.0 therefore deliberately makes carrier-level claims only.
