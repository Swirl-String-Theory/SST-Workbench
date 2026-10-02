# Paper-driven upgrade stage

This additive stage is intentionally isolated from the existing solver implementation.
It is designed to be applied to the canonical migrated family directory and validated independently before wiring into the primary run chain.

Scientific policy:
- do not import Hall-effect microphysics into SST; only symmetry-selection methodology is transferred;
- do not import a string-theory swampland bound into SST; only admissibility/no-go methodology is transferred;
- all thresholds remain preregistered/numerically certified, not tuned to obtain a positive SST outcome;
- existing blind/reveal and output-archive conventions remain authoritative.

Family: **A031 — Adaptive Period RPO/Floquet**
Base: `v0.1.0`
Target: `v0.2.0`
Priority: `P1`
Paper inspiration: arXiv:2505.06829 + 1806.08362 — upstream certificates and downstream qualification.

## Added gates
Same physical contract as A023, but enforced inside adaptive-period/multiple-shooting qualification. Period adaptation may not absorb a mirror-parity failure.

## Falsification discipline
A paper-inspired gate is considered useful only if it can return FAIL/NULL/INDETERMINATE independently of SST expectations. Absolute threshold values must be preregistered or certified using target-free synthetic/numerical benchmarks.
