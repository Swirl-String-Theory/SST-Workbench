# Paper-driven upgrade stage

This additive stage is intentionally isolated from the existing solver implementation.
It is designed to be applied to the canonical migrated family directory and validated independently before wiring into the primary run chain.

Scientific policy:
- do not import Hall-effect microphysics into SST; only symmetry-selection methodology is transferred;
- do not import a string-theory swampland bound into SST; only admissibility/no-go methodology is transferred;
- all thresholds remain preregistered/numerically certified, not tuned to obtain a positive SST outcome;
- existing blind/reveal and output-archive conventions remain authoritative.

Family: **A024 — Threaded Hole / Separatrix**
Base: `v0.3.0`
Target: `optional-paper-control`
Priority: `optional`
Paper inspiration: arXiv:2505.06829 — symmetry, mirror parity, forbidden-response nulls, covariance.

## Optional control
Add mirror/body-frame covariance diagnostics as secondary controls. They may invalidate an apparent effect, but cannot create a primary PASS on their own.

## Falsification discipline
A paper-inspired gate is considered useful only if it can return FAIL/NULL/INDETERMINATE independently of SST expectations. Absolute threshold values must be preregistered or certified using target-free synthetic/numerical benchmarks.
