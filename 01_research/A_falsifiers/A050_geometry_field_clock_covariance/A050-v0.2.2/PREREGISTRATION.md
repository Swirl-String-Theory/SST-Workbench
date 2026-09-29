# A050-v0.2.2 — Frozen preregistration

**Long-Horizon Modal Persistence + Temporal-Memory Convergence Gate**

Status: **FROZEN BEFORE SCIENTIFIC RUN**.

v0.2.2 is confirmatory. The v0.2.1 base trajectories are discovery material and do not control the primary modal-persistence verdict. The confirmatory modal channel uses 20 pre-generated, hash-locked perturbation carriers arranged as four anonymous groups of five. Geometry identities and perturbation seeds remain reveal-only.

## Frozen horizons

- spatial qualification: 80 evolution steps;
- temporal-memory trajectory: 1024 evolution steps, sampled every 4 steps;
- modal-persistence trajectory: 2048 evolution steps;
- modal checkpoints: 320, 640, 1024, 1536, 2048;
- late confirmatory checkpoints: 640, 1024, 1536, 2048.

## Legacy gates

All v0.2.0 spatial, temporal-memory, and transverse-mode thresholds are loaded unchanged from `config/frozen_gate_thresholds_v0.2.0.json`. v0.2.2 must not retune them after observing results.

## Modal persistence gate

A holdout carrier is persistent only if one transverse branch qualifies at at least 3 of 4 late checkpoints, the 2048-step checkpoint qualifies, and the coefficient of variation of its measured frequency is at most 0.15. An anonymous group is confirmed only if at least 4 of its 5 carriers support the same persistent branch. At least one anonymous group must confirm.

For every confirmed group, the lowest carrier ID among the supporting persistent carriers is selected by a predeclared deterministic rule for numerical convergence. Curve-point ladder: 56, 72, 96. Timestep ladder: 0.02, 0.01 at the same dimensionless end time. The modal branch must remain qualified and identical; frequency relative span must be <=0.15.

## Temporal-memory convergence gate

Nested windows are fixed at 80, 160, 320, 640, 1024 evolution steps. The original shuffled-null memory gate must pass at the final two windows. The integrated memory time uses a pairwise initial-positive-sequence estimator. Its final-window relative change must be <=0.25, and the 95% circular-block-bootstrap intervals must overlap. At least two base families must converge.

A Fourier phase-randomized surrogate is generated as a diagnostic only. It is not used as an ACF-null because preserving the power spectrum preserves two-point autocorrelation structure.

## Floquet policy

No adaptive Floquet/RPO search is active in v0.2.2. v0.2.1 ended without a qualified preregistered recurrence. A future RPO/true-Floquet campaign requires a separate frozen protocol.

## Allowed primary verdicts

- `NUMERICAL_QUALIFICATION_FAILED`
- `TEMPORAL_MEMORY_NOT_REPRODUCED`
- `TEMPORAL_MEMORY_PRESENT_NOT_CONVERGED`
- `MODAL_PERSISTENCE_NOT_REPRODUCED`
- `MODAL_PERSISTENCE_NONCONVERGENT`
- `STRUCTURED_MEMORY_AND_MODAL_PERSISTENCE_CONFIRMED`

The seal in `config/SEAL_v0.2.2.json` locks the preregistration, primary config, holdout manifest and primary analysis implementation before a scientific run.
