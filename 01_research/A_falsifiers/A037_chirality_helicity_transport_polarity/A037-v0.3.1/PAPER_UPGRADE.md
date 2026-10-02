# Paper-driven upgrade stage

This additive stage is intentionally isolated from the existing solver implementation.
It is designed to be applied to the canonical migrated family directory and validated independently before wiring into the primary run chain.

Scientific policy:
- do not import Hall-effect microphysics into SST; only symmetry-selection methodology is transferred;
- do not import a string-theory swampland bound into SST; only admissibility/no-go methodology is transferred;
- all thresholds remain preregistered/numerically certified, not tuned to obtain a positive SST outcome;
- existing blind/reveal and output-archive conventions remain authoritative.

Family: **A037 — Chirality–Helicity Transport Polarity**
Base: `v0.2.0`
Target: `v0.3.0`
Priority: `P0`
Paper inspiration: arXiv:2505.06829 — symmetry, mirror parity, forbidden-response nulls, covariance.

## Added gates
1. Build a body-frame symmetry-selection matrix before trajectory integration.
2. Measure central-difference response tensor and split into symmetric/antisymmetric sectors.
3. Require analytically forbidden components to converge to zero.
4. Repeat after rigid rotations and test covariance instead of coordinate-specific agreement.
5. Keep mirror pairs as one statistical unit.

## Falsification discipline
A paper-inspired gate is considered useful only if it can return FAIL/NULL/INDETERMINATE independently of SST expectations. Absolute threshold values must be preregistered or certified using target-free synthetic/numerical benchmarks.
