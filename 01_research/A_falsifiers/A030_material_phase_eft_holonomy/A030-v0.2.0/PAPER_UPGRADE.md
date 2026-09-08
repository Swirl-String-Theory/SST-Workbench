# Paper-driven upgrade stage

This additive stage is intentionally isolated from the existing solver implementation.
It is designed to be applied to the canonical migrated family directory and validated independently before wiring into the primary run chain.

Scientific policy:
- do not import Hall-effect microphysics into SST; only symmetry-selection methodology is transferred;
- do not import a string-theory swampland bound into SST; only admissibility/no-go methodology is transferred;
- all thresholds remain preregistered/numerically certified, not tuned to obtain a positive SST outcome;
- existing blind/reveal and output-archive conventions remain authoritative.

Family: **A030 — Material Phase EFT / Holonomy**
Base: `v0.1.1`
Target: `v0.2.0`
Priority: `P1`
Paper inspiration: arXiv:2505.06829 — symmetry, mirror parity, forbidden-response nulls, covariance.

## Added gates
Define gauge-invariant mode transport in parameter space: normalize with a weight matrix, parallel-transport the phase, compute closed-loop geometric phase, and compute plaquette curvature. This is the correct Berry-inspired analogue; hydrodynamic vorticity itself is not identified with Berry curvature.

## Falsification discipline
A paper-inspired gate is considered useful only if it can return FAIL/NULL/INDETERMINATE independently of SST expectations. Absolute threshold values must be preregistered or certified using target-free synthetic/numerical benchmarks.
