# Changelog

## v0.4.0-alpha.1

- begins closure-robustness and fine-tuning analysis;
- adds a deterministic 4-term closure simplex scanner;
- distinguishes screening fractions from full-Hessian stability claims;
- adds a Borromean triple-sector ledger for all eight circulation assignments;
- records `|mu-bar_123|=1` as a catalog reference only, not a numerical result;
- documents the remaining route to v0.4.0 final.

# Changelog

## v0.3.2

- identifies `L6a4` as the **Borromean rings** in the catalog ledger;
- separates `topology_sample_n` from the reduced-QM grid;
- flags every multi-component pairwise-zero link, including two-component cases;
- retains every `2^m` circulation assignment and stops quotienting by unproven automorphism proxies;
- replaces per-sector energy normalization by preregistered fixed reference scales;
- records gradient cancellation ratios and closure-balance warnings;
- distinguishes diagonal-Hessian screening from full-Hessian stability claims;
- adds optional finite-difference step-halving convergence in full/max presets;
- fixes suite-version provenance;
- fixes the Windows double-force-build `.pyd` lock;
- adds scale-derivation and regression tests.


# Changelog

## v0.3.1

Windows native-startup hotfix:

- explicit same-interpreter native preflight in `run_qm.cmd` and `run_qm.ps1`;
- clean extractions build their ABI-specific `.pyd` before `--require-native`;
- complete compiler output is shown instead of swallowed;
- runner forwards native build-control flags;
- backend errors include interpreter, Python ABI, extension path, and lower-level cause;
- chunked builds are strict and verbose;
- regression tests cover the runner/preflight contract.

# Changelog

## v0.3.0

### Added

- Independent QM-readiness campaign and CLI.
- Integer linking-form ledger and circulation-sector quotient under component automorphisms and global reversal.
- Explicit flag for three-component links whose pairwise Gauss linking cannot resolve higher linking.
- Periodic rotation-minimizing normal frames and normal-bundle holonomy.
- Low-harmonic normal perturbation basis with rigid translation/rotation gauge removal.
- Termwise finite-difference gradients and Hessians for length, bending, tube repulsion and regularized Neumann energy.
- Reuse of geometric derivatives across circulation sectors to avoid repeated expensive evaluations.
- Rasetti–Regge-type candidate reduced filament two-form with rank/nullity audit.
- Linearized Hamiltonian generator, stability test and dimensionless frequency ratios.
- Sequential Q1–Q5 readiness verdicts.
- CSV reports for topological labels, sectors, normal modes, candidate symplectic forms and holonomy.
- `qm_quick`, `qm_full` and `qm_max` presets.

### Preserved

All v0.2.1 geometry, contact-map, C++17/pybind11 Biot–Savart, parity and Ridgerunner bridge functionality remains available.

### Interpretation boundary

The new machinery is Research Track. It does not derive Hilbert space, Born probabilities, operator
algebras, \(\hbar\), or measured particle spectra. Energy-profile weights remain explicit assumptions.
