# Paper-driven upgrade stage

This additive stage is intentionally isolated from the existing solver implementation.
It is designed to be applied to the canonical migrated family directory and validated independently before wiring into the primary run chain.

Scientific policy:
- do not import Hall-effect microphysics into SST; only symmetry-selection methodology is transferred;
- do not import a string-theory swampland bound into SST; only admissibility/no-go methodology is transferred;
- all thresholds remain preregistered/numerically certified, not tuned to obtain a positive SST outcome;
- existing blind/reveal and output-archive conventions remain authoritative.

Family: **A023 — MultiTopology RPO/Floquet**
Base: `v0.4.8`
Target: `v0.5.0`
Priority: `P1`
Paper inspiration: arXiv:2505.06829 + 1806.08362 — upstream certificates and downstream qualification.

## Added gates
Require A034 admissibility before RPO search; construct true monodromy only around a periodic/relative-periodic base state; compare mirror-related monodromy spectra under the preregistered symmetry transform.

## Falsification discipline
A paper-inspired gate is considered useful only if it can return FAIL/NULL/INDETERMINATE independently of SST expectations. Absolute threshold values must be preregistered or certified using target-free synthetic/numerical benchmarks.
