# Paper-driven upgrade stage

This additive stage is intentionally isolated from the existing solver implementation.
It is designed to be applied to the canonical migrated family directory and validated independently before wiring into the primary run chain.

Scientific policy:
- do not import Hall-effect microphysics into SST; only symmetry-selection methodology is transferred;
- do not import a string-theory swampland bound into SST; only admissibility/no-go methodology is transferred;
- all thresholds remain preregistered/numerically certified, not tuned to obtain a positive SST outcome;
- existing blind/reveal and output-archive conventions remain authoritative.

Family: **A021 — Trefoil Lobe Self-Confinement**
Base: `v0.3.0`
Target: `v0.4.0-consumer`
Priority: `P2`
Paper inspiration: arXiv:1806.08362 — admissibility, constrained landscape, no-go directions, soft modes.

## Added contract
Do not implement a second landscape/Hessian solver in A021. Self-confinement promotion requires a qualified A034 admissibility certificate; historical A021 results remain preserved.

## Falsification discipline
A paper-inspired gate is considered useful only if it can return FAIL/NULL/INDETERMINATE independently of SST expectations. Absolute threshold values must be preregistered or certified using target-free synthetic/numerical benchmarks.
