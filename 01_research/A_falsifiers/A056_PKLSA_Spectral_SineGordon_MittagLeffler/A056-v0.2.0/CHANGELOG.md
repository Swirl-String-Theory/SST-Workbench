# Hotfix 1 — 2026-10-07

- Fixed default output-directory divergence when installed under the canonical Workbench folder `A056-v0.2.0`.
- `a056_falsifier.pipeline`, reveal, report and packaging now share `sst_falsifier_framework.outputs.default_output_dir(ROOT)`.
- Added regression test for renamed/version-folder deployments.
- Scientific equations, thresholds, blind commitments and model-selection logic are unchanged.

# Changelog

## v0.2.0

- First trial consumer of `SST Falsifier Framework v1.0.0.dev0`.
- Replaced single-stage CV scoring with frozen discovery/held-out confirmation lanes.
- Added strict dynamic PKLSA/Euler provider contract and provenance hashes.
- Added deterministic resolution certification and CPU/native parity gate.
- Added optional out-of-process SYCL/oneAPI worker probe; GPU remains screening-only.
- Added dependency-aware framework gate ledger.
- Added mandatory LaTeX falsifier report template and automatic BLIND report generation.
- Preserved the v0.1.0 five-case synthetic control population for regression validation, with upgraded metadata.
