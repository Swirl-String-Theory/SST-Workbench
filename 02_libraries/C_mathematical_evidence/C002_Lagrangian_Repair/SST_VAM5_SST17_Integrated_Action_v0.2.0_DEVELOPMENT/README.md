# SST VAM-5 + SST-17 Integrated Action v0.2.0

**Qualification:** `DEVELOPMENT / NOT PHYSICALLY CERTIFIED`  
**Date:** 2026-10-20  
**Original sources:** VAM-5 (Zenodo DOI `10.5281/zenodo.15772858`), SST-17 (DOI `10.5281/zenodo.17677074`), v0.1.0 constrained Euler repair. Historical originals have not been modified.

## Files

- `SST_VAM5_SST17_Integrated_Action_v0.2.0.pdf`: self-contained 9-page scientific report, all equations, assumptions, gate table, citations.
- `SST_VAM5_SST17_Integrated_Action_v0.2.0.tex`: editable, copy-ready source.
- `tests/validate_integrated.py`: **47 deterministic diagnostic regression tests** (Python + NumPy + SymPy).
- `results/validation_report.json`: full individual test status, numerical residuals, gates, and numerical constants.
- `source_manifest.json`: SHA256 of the inspected historical source PDFs (source PDFs intentionally excluded from the bundle).
- `science_contract.json`: mathematical scope, modelling choices, dimensions, and nonpromotion rules.
- `gate_definitions.json`: G0–G6 success contracts and explicit non-executed stages.
- `run_all.cmd`, `run_all.sh`: portable regression and optional PDF rebuilding, respectively on Windows and Linux/macOS.
- `CHANGELOG.md`, `requirements.txt`, `SHA256SUMS.txt`.

## Run

Windows:

```bat
run_all.cmd
run_all.cmd PDF
```

Linux/macOS:

```bash
bash run_all.sh
bash run_all.sh PDF
```

The first mode runs the regression suite and updates `results/validation_report.json`. The `PDF` option additionally runs `latexmk` if installed. For numerical dependencies, use `python -m pip install -r requirements.txt` (local only).

The supplied PDF is already compiled; LaTeX installation is optional for running tests.

## What was integrated?

The fluid is represented by an incompressible material map `X(a,t)`. A **new independent** vector displacement `q(a,t)` carries linear transverse wave dynamics. The spatial curls and divergences of `q` depend on the deformation gradient of `X`, creating a legitimate variationally specified coupling (not just a direct sum). The associated canonical momenta, backreaction stress and Hamiltonian are all explicit.

On a frozen uniform background, the q wave maps to **source-free** Maxwell equations after an SI field calibration. That mathematical equivalence **does not derive** Maxwell dynamics from Euler; `rho_d` and `K` are extra constitutive inputs, and c is explicitly calibrated rather than predicted. The Cartan torsion projection is a kinematic closed 2-form. An optional gyroscopic demonstration resembles Faraday rotation but has no derived magnetic microphysics.

## Current test scope and exclusions

The tests include a finite-difference variation of the coupled action w.r.t. both gradients, rigid objectivity, incompressible Euler/pressure null controls, source-free Maxwell identities, polarization counting, and **1D frozen-fluid** leapfrog wave time convergence. **They do not integrate the full 3D coupled PDE or native PKLSA knots.** No experimental electromagnetic, gravitational, photon, charge, spin, quantum or particle-mass claim is certified.

To integrate with SST-Workbench, pass `source_manifest.json`, `science_contract.json`, and `gate_definitions.json` to a future **framework-controlled** source-native PKLSA implementation. Do not interpret this standalone package as a frozen falsifier-framework instance or as modifying an existing canonical codebase.
