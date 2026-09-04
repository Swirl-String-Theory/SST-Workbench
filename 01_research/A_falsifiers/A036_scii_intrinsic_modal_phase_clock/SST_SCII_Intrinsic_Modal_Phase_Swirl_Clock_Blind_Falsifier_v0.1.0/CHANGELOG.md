# Changelog

## v0.1.0 — SC-II Intrinsic Modal Phase Swirl Clock

New standalone falsifier derived from the certified v0.2.2.x modal workbench.

### New hypothesis

- Separates SC-II intrinsic modal **phase** recurrence from SC-I full-shape
  recurrence.
- Full centerline closure after one period is no longer required.
- Primary variable is `phi_sc(t)`, the unwrapped analytic phase of a frozen
  intrinsic modal coordinate.

### New blind Stage-A gates

- minimum intrinsic discovery energy and amplitude;
- >=4 phase wraps in BASIC;
- >=90% monotone phase progression;
- phase-linearity R² >=0.90;
- period CV <=0.15;
- spectral/harmonic support;
- one-cycle phase-diffusion bound;
- envelope persistence/ringdown rejection;
- calibration-to-holdout phase prediction;
- mandatory natural channel.

### Certification

- low/high mesh-gauge replay reuses frozen Stage-A spatial modes;
- provenance robustness is source-family balanced;
- Fremlin variants remain separate shapes but one provenance vote.

### Stage B

- tests delayed stretch -> instantaneous phase-velocity modulation;
- evaluates delay advantage over zero lag;
- phase-shift null p-value;
- material-core specificity against fixed core.

### Workflow

- added `analyze-sc2-stage-a`, `analyze-sc2-gauge`,
  `analyze-sc2-provenance`, `analyze-sc2-stage-b` CLI commands;
- added `run_sc2_from_stage_a.cmd` to reuse expensive existing T=24 data;
- full and focus workflows now run SC-II analysis;
- existing progress/ETA logging retained.

### Validation

- 58 Python/regression tests pass;
- clean synthetic persistent phase clock passes all SC-II Stage-A gates;
- synthetic severe ringdown fails envelope gate;
- chirped oscillator fails clock-coherence/prediction gate;
- odd probe mode can never become a primary SC-II candidate;
- synthetic end-to-end workbench reaches provisional and mesh-gauge-certified
  SC-II PASS, while an uncoupled Stage-B null correctly fails the mechanism;
- real-data regression on 13 previously geometry-certified carriers returned
  zero natural-channel SC-II candidates without threshold changes;
- C++ physics kernel is inherited unchanged from the v0.2.2.8 base.
