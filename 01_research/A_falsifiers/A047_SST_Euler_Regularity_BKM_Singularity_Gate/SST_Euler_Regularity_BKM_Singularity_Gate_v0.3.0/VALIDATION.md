# Validation — SST Euler Regularity / BKM Singularity Gate v0.3.0

## Upstream E010 evidence inspected

Latest PKLSA v0.3.x located in the Google Drive SST-Workbench: **E010 / PKLSA v0.3.1**, release dated 2026-09-25.

The inspected production release reports source-native mode and green source-contract, A001--A008 coverage, canonical-identity, identity-database, topology-database and trefoil-POC gates. The global all-topology campaign is not publication-ready (`failed_topology_count=1373` across `topology_count=2227`), so A047 scopes admission to the separately qualified `3_1` POC.

The inspected trefoil POC reports 189 discovered/qualified carriers, 0 carrier errors and 7 E010 independence groups. Its source matrix includes KnotPlot relaxed/Fourier/QHP, Fremlin Fourier, Gilbert ideal and PTSA carriers plus mirrors. E010's POC literature mode is `report` and records 25 hard-gate failures; A047 v0.3.0 excludes those failures by default and also removes recorded mirrors/raw/geometry duplicates. On the inspected frozen output this leaves 116 geometries.

## Package tests

Run `python -m pytest -q`. Tests cover:

1. trefoil-scoped E010 release gating even when the unrelated all-topology aggregate gate is red;
2. G1/G2/G3 hard-failure, mirror and duplicate exclusion;
3. relocated Windows Workbench path resolution;
4. exact E010 geometry hash contract;
5. centerline canonicalization + native vorticity initialization;
6. convergence isolation so distinct geometries cannot be pooled;
7. legacy spectral projection and ABC/Beltrami regression;
8. Windows/MSVC no-bare-`ssize_t` source regression.

## Scientific run status in this package build environment

A full E010-v0.3.1 scientific Euler campaign is **not run here**, because the production carrier envelopes intentionally reference original source bytes in the user's local SST-Workbench. A047 fails closed if those bytes or their recorded hashes are unavailable. The local user run is therefore the authoritative scientific execution.

## Build-environment validation performed for this release

- Native C++17/pybind11 extension compiled successfully with the available local pybind11 headers.
- `pytest`: **10 passed**.
- The actual 102.9 MB E010-v0.3.1 production outputs ZIP was integrity-tested (`ZipFile.testzip() -> None`).
- The runtime selector was executed against the real extracted E010 `3_1` POC ledgers: 189 qualified input carriers -> **116 admitted geometries in 5 admitted independence groups** under the default guard.
- Real-ledger default exclusions were classified as 31 non-independent mirrors, 17 literature-hard-gate failures (after mirror precedence) and 25 remaining raw/geometry duplicates; the upstream summary itself records 25 total literature-hard-gate-failing carriers before other exclusions.

A synthetic source-native end-to-end fixture then exercised `RELEASE -> carrier envelope -> original source bytes -> raw SHA -> E010 geometry SHA -> canonicalization -> native vorticity tube -> Euler -> BLIND aggregation`. Result: 1/1 numerically valid, energy relative drift `2.21e-11`, maximum divergence RMS `1.95e-16`, no BKM candidate in the short smoke window. The BLIND provenance leakage scan passed for carrier ID, source path, source family/provider/lineage/method labels and catalog-source identity.

The synthetic smoke is a software integration test only; it is not physical evidence. The full local E010-v0.3.1 source-native run remains the scientific execution.
