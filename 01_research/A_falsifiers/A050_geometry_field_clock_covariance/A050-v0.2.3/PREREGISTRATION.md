# A050-v0.2.3 — Frozen diagnostic preregistration

## Local Basin / Perturbation-Sensitivity Map around G0002

Status: **FROZEN BEFORE THE v0.2.3 SCIENTIFIC RUN**.

v0.2.3 is intentionally **post-confirmatory**. It was motivated by the revealed v0.2.2 result: the primary v0.2.2 verdict was `MODAL_PERSISTENCE_NOT_REPRODUCED`; H04 mapped to G0002; C00016 supported a strict persistent m=3 branch while C00020 reached 4/4 late checkpoints but failed the frozen frequency-CV criterion. This selection makes v0.2.3 a mechanism diagnostic, not an independent confirmation. It cannot change the v0.2.2 verdict.

### Frozen question

Does the G0002 m=3 transverse branch occupy a finite-radius local neighborhood under the unchanged v0.2.2 dynamics and modal thresholds, or is the observed behavior isolated / narrow / anisotropic?

### Frozen dynamics

- generated dimensionless G0002 base curve;
- 56 curve points;
- regularization/core ratio 0.1;
- time step 0.02;
- reparameterization every 2 steps;
- 2048 evolution steps;
- checkpoints 320, 640, 1024, 1536, 2048;
- late checkpoints 640, 1024, 1536, 2048;
- all legacy transverse-mode thresholds are copied unchanged from v0.2.0/v0.2.2.

### Perturbation map

Twelve fixed, hash-locked transverse Fourier directions are generated before the run. Every direction is reused at every nonzero amplitude (paired-direction design). No direction may be removed after results are observed.

Nominal RMS amplitudes are:

`0, 0.00125, 0.0025, 0.00375, 0.005, 0.0075, 0.01`.

The nonzero map therefore contains 72 trajectories, plus one unperturbed baseline. The original v0.2.2 perturbation scale 0.005 is bracketed on both sides.

### Frozen local-basin gate

The unperturbed baseline must satisfy the unchanged strict persistence rule on branch m=3. At each core amplitude 0.00125 and 0.0025, at least 9 of 12 directions must satisfy that same strict m=3 persistence rule. The cross-direction coefficient of variation of the qualifying mean m=3 frequency must be <= 0.20 at each core amplitude.

Outer amplitudes 0.00375, 0.005, 0.0075 and 0.01 map the loss or continuation of support but do **not** decide the primary local-core gate.

If a finite-radius core is supported, the lowest direction ID among strict m=3 members at epsilon=0.0025 is used for a deterministic numerical-convergence check: curve points 56/72/96 and time steps 0.02/0.01 at identical end time; target branch m=3 must remain qualified and the frequency relative span must be <=0.15.

### Allowed verdicts

- `BASELINE_M3_NOT_PERSISTENT`
- `ISOLATED_M3_TRAJECTORY_BEHAVIOR`
- `NARROW_OR_ANISOTROPIC_M3_BASIN`
- `LOCAL_M3_BASIN_FREQUENCY_NONROBUST`
- `FINITE_RADIUS_M3_BASIN_NONCONVERGENT`
- `FINITE_RADIUS_M3_BASIN_SUPPORTED`

None of these verdicts supersedes the parent v0.2.2 verdict.

### Explicit exclusions

No temporal-memory retesting, no Floquet/RPO search, no SST absolute constants, no threshold retuning, no carrier cherry-picking, and no post-run replacement of directions or core amplitudes are permitted in v0.2.3.
