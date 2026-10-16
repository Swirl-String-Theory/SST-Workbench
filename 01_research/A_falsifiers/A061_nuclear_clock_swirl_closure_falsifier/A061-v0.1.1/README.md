# A061 Nuclear Clock / Swirl Clock Closure Falsifier v0.1.1

**Canonical runtime: exact SST Falsifier Framework v1.0.7, profile `cpu`.**

This is a regenerated official-framework instance that retains the A061-v0.1.0 physics equations, source PDFs and source summaries, but uses the actual frozen framework's protocol, gate ledger, manifest, blind/reveal controls and backend construction. It is not evidence of SST clock physics. G3 audits an internal source-level discrepancy and does not condemn all SST.

## Install

Extract this `A061-v0.1.1` directory under:
`SST-Workbench/01_research/A_falsifiers/A061_nuclear_clock_swirl_closure_falsifier/A061-v0.1.1`.
Extract the user's unmodified `SST_Falsifier_Framework_v1.0.7-CANONICAL_FROZEN.zip` at `SST-Workbench/06_templates/SST_Falsifier_Framework/` so that `SST_Falsifier_Framework_v1.0.7` is directly beneath it. Verify its SHA-256: `139800c75be8fea0b581c3a7c5db96d29c9231d7b9e30e9fdbc1888e741a6462`.

## Run (Windows)

`run_all.cmd SETUP` -- install numpy, pytest, pybind11, setuptools via instance venv.
`run_all.cmd SELFTEST` -- framework regressions plus A061 scientific tests.
`run_all.cmd FREEZE` -- already frozen, verifies unchanged preregistration.
`run_all.cmd BASIC` -- real published-summary mathematical gates, servo controls, optional native parity.
`run_all.cmd FETCH` -- download Zenodo and Figshare raw data (internet required).
`run_all.cmd BUILD_NATIVE` -- strict official pybind11/C++17 numerical kernel.
`run_all.cmd FULL` -- attempt raw analysis; missing source => UNRESOLVED.
`run_all.cmd CERTIFY` -- run all science gates; returns a nonzero exit code unless strict numerical and physical closure gates pass.
`run_all.cmd REVEAL_IF_ALLOWED` -- normally WITHHELD; unresolved physics gates prevent disclosure.

G0--G13 are independent gates (`requires: []`) to honor the science-specific continue-on-failure requirement. Framework integrity failures still stop before blind science; this is deliberate. G6 GPU screening and G7 multi-library replication are disabled under CPU profile. Official BLIND packages are created by Framework v1.0.7 within the instance parent folder.

Evidence classes: published experimental summaries, synthetic controls, optional real time-series. A passed synthetic/algorithm test cannot validate an SST physical hypothesis. Nuisance/environment identifiability and non-SST feedback effects are tested separately. No parameter tuning against source data is permitted in a physical SST prediction gate.

Datasets: Toscani De Col et al. `10.1038/s41586-026-11084-4` (Zenodo `10.5281/zenodo.22657608`); Huang et al. `10.1038/s41586-026-11122-1` (Figshare `10.6084/m9.figshare.33386191`). Core theory: SST-28 `10.5281/zenodo.17877012`.

The official instance itself is **not** the framework, and this release deliberately does not vendor or mutate canonical v1.0.7. Files `preregistration/FROZEN_PROTOCOL.json` and the private commitments are created by framework `FREEZE`, never by the standalone runner.
