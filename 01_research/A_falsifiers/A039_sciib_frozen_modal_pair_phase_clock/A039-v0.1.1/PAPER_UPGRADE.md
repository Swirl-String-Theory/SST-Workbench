# Paper-driven upgrade stage

This additive stage is intentionally isolated from the existing solver implementation.
It is designed to be applied to the canonical migrated family directory and validated independently before wiring into the primary run chain.

Scientific policy:
- do not import Hall-effect microphysics into SST; only symmetry-selection methodology is transferred;
- do not import a string-theory swampland bound into SST; only admissibility/no-go methodology is transferred;
- all thresholds remain preregistered/numerically certified, not tuned to obtain a positive SST outcome;
- existing blind/reveal and output-archive conventions remain authoritative.

Family: **A039 — SCIIb Frozen Modal Pair Subspace Phase Clock**
Base: `v0.1.1`
Target: `DEFERRED_AFTER_A030`
Priority: `deferred`
Paper inspiration: arXiv:2505.06829 — symmetry, mirror parity, forbidden-response nulls, covariance.

## Deferred migration guard
No phase-definition change is made here. This patch only installs a machine-checkable dependency guard requiring a qualified A030 `SST-GEOMETRIC-PHASE-1.0` certificate.

## Falsification discipline
A paper-inspired gate is considered useful only if it can return FAIL/NULL/INDETERMINATE independently of SST expectations. Absolute threshold values must be preregistered or certified using target-free synthetic/numerical benchmarks.
