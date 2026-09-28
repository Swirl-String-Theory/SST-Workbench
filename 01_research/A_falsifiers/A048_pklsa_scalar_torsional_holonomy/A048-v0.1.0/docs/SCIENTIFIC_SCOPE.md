# Scientific scope and falsification boundary

A048 v0.1.0 intentionally separates three layers:

1. **Orthodox numerical controls:** periodic curve geometry, curvature/torsion, Kelvin-like quadratic dispersion fit, gauge/winding invariance.
2. **Derived analysis machinery:** blind model selection and PKLSA ingest/canonicalization.
3. **Speculative SST hypothesis:** an independent internal material-phase/torsional eigenbranch whose dispersion approaches \(\omega\propto k\) rather than the Kelvin-like \(\omega\propto k^2\) law.

The v0.1.0 pass/fail result is only an instrument-qualification statement. A future release must ingest independently generated finite-core dynamics and test whether a distinct branch exists after convergence and leakage controls.

## Minimal next experiment

For each of the 48 PKLSA trefoils, initialize at least two independent perturbation families:

- transverse centerline displacement;
- internal/core phase or material-marker perturbation.

Evolve with a finite-core solver, record both observables, extract modal frequencies and cross-spectral coherence, then compare the measured branches to quadratic Kelvin and linear/gapped torsional models without injecting either law into the dynamics.
