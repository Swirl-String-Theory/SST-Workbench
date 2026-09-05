# Changelog

## v0.3.3

- adds fixed **physical arc-length** self-exclusion to native and NumPy Biot–Savart/Neumann kernels;
- adds C++/NumPy parity tests for the new arc-exclusion kernels;
- removes v0.3.2 sample-derived energy reference scales from default QM presets;
- uses diameter-dimensionalized energy terms: `L/D`, `D*bending`, dimensionless repulsion, `E_N/D`;
- adds `scripts/run_continuum.py`, `run_continuum.cmd`, and `run_continuum.ps1`;
- adds N-refinement ledgers and optional Richardson estimates;
- adds candidate-symplectic nullspace diagnostics and an algebraic image-space quotient spectrum;
- adds a trust-limited Newton stationarity probe for the best full/max sector;
- records catalog `|mu-bar_123|=1` for `L6a4` / Borromean rings without marking it numerically computed;
- preserves all `2^m` circulation sectors;
- suite provenance updated to `0.3.3`.

## v0.3.2

- identifies `L6a4` as the **Borromean rings** in the catalog ledger;
- separates `topology_sample_n` from the reduced-QM grid;
- flags every multi-component pairwise-zero link, including two-component cases;
- retains every `2^m` circulation assignment and stops quotienting by unproven automorphism proxies;
- replaces per-sector energy normalization by preregistered fixed reference scales;
- records gradient cancellation ratios and closure-balance warnings;
- distinguishes diagonal-Hessian screening from full-Hessian stability claims;
- adds optional finite-difference step-halving convergence in full/max presets;
- fixes suite-version provenance and the Windows double-force-build `.pyd` lock.

## v0.3.1

- same-interpreter Windows native preflight;
- verbose build diagnostics and native flag passthrough.

## v0.3.0

- initial Q1–Q5 reduced QM-readiness campaign;
- normal perturbation basis, Hessians, candidate two-form and linearized spectrum.
