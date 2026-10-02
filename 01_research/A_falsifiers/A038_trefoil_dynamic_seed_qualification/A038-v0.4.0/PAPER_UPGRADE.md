# Paper-driven upgrade stage

This additive stage is intentionally isolated from the existing solver implementation.
It is designed to be applied to the canonical migrated family directory and validated independently before wiring into the primary run chain.

Scientific policy:
- do not import Hall-effect microphysics into SST; only symmetry-selection methodology is transferred;
- do not import a string-theory swampland bound into SST; only admissibility/no-go methodology is transferred;
- all thresholds remain preregistered/numerically certified, not tuned to obtain a positive SST outcome;
- existing blind/reveal and output-archive conventions remain authoritative.

Family: **A038 — Trefoil Dynamic Seed Qualification Mega**
Base: `v0.3.3`
Target: `v0.4.0`
Priority: `P0`
Paper inspiration: arXiv:2505.06829 + 1806.08362 — upstream certificates and downstream qualification.

## Added contract
A038 becomes a certificate consumer. Expensive downstream dynamics are authorized only after valid geometry, mesh, A034-admissibility and A037-symmetry certificates are present. No A034/A037 physics is duplicated here.

## Falsification discipline
A paper-inspired gate is considered useful only if it can return FAIL/NULL/INDETERMINATE independently of SST expectations. Absolute threshold values must be preregistered or certified using target-free synthetic/numerical benchmarks.
