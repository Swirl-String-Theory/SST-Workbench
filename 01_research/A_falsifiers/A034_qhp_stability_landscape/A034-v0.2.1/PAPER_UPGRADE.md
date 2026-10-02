# Paper-driven upgrade stage

This additive stage is intentionally isolated from the existing solver implementation.
It is designed to be applied to the canonical migrated family directory and validated independently before wiring into the primary run chain.

Scientific policy:
- do not import Hall-effect microphysics into SST; only symmetry-selection methodology is transferred;
- do not import a string-theory swampland bound into SST; only admissibility/no-go methodology is transferred;
- all thresholds remain preregistered/numerically certified, not tuned to obtain a positive SST outcome;
- existing blind/reveal and output-archive conventions remain authoritative.

Family: **A034 — QHP Stability Landscape**
Base: `v0.1.3`
Target: `v0.2.0`
Priority: `P0`
Paper inspiration: arXiv:1806.08362 — admissibility, constrained landscape, no-go directions, soft modes.

## Added gates
1. Project the first variation onto the constraint tangent space.
2. Evaluate an augmented-energy branch only for invariants supported by the active dynamics.
3. Search preregistered tangent directions for one-sided no-go derivatives.
4. Restrict the Hessian to the tangent space and classify energetic saddles/soft modes.
5. Keep the existing QHP vector-field Jacobian as an independent dynamical-stability test; do not equate Hessian positivity with Floquet stability.

## Falsification discipline
A paper-inspired gate is considered useful only if it can return FAIL/NULL/INDETERMINATE independently of SST expectations. Absolute threshold values must be preregistered or certified using target-free synthetic/numerical benchmarks.
