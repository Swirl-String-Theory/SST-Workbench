# Cross-campaign lessons incorporated into v0.2.0

This document separates **prior campaign observations** from **changes made in this package**. The earlier observations are motivation; they are not v0.2.0 results.

## 1. QHP Stability Landscape

**Prior observation.** Low-dimensional Q/H/P restoring coordinates did not produce a robust resolution-common restoring structure in the studied campaigns. The methodology itself also required fixes so a sign crossing counted only when projection/basis quality, actual short-time crossing and independent confirmation were all valid.

**v0.2.0 consequence.** Q/H/P coordinates and low POD dimensionality are not ranking priors. POD rank is exported as a diagnostic with zero score weight. Seed quality is measured directly from the full normal-space rolling/deformation signal.

## 2. Moving trefoil balance-point campaign

**Prior observation.** A tempting scalar zero/balance point moved as the trajectory was extended; it did not certify a fixed geometric equilibrium.

**v0.2.0 consequence.** No static scalar `Rg`, energy-zero or one-coordinate crossing can qualify a seed. A seed must pass dynamical rolling, numerical robustness and later orbital-return gates.

## 3. Phase-feedback / pseudoreplication audit

**Prior observation.** A nominal 41-file dataset contained far fewer unique geometries, including large byte-identical blocks; retrospective deduplication changed the apparent correlation substantially.

**v0.2.0 consequence.** S10 performs geometry-aware source dedup and source-stratified scheduling before ranking. Later promotion also preserves source-group coverage where possible.

## 4. Intrinsic Modal Swirl-Clock long-horizon campaign

**Prior observation.** The initial long-horizon recurrence search was dominated by Lagrangian bead-spacing degradation; a later numerical-certification release introduced uniform-arclength/cyclic/rigid/normal analysis, segment-feedback tangential redistribution, an RMS mesh-speed cap and mesh-gauge replay.

**v0.2.0 consequence.** Those numerical ideas are moved into the seed-qualification chain itself. New S37 must certify mesh-gauge robustness before S40. S40 shape analysis is parameterization-invariant, and numerical coverage is separated from physics verdicts.

## 5. Finite-core axial/toroidal phase-delay campaigns

**Prior observation.** A self-generated propagation delay can be measured accurately without supplying a delay, but propagation timing alone did not establish a phase-stability mechanism.

**v0.2.0 consequence.** The phase is never used for seed ranking or orbital existence. S60 runs only after S50 and treats measured phase as output. A mechanism requires held-out causal predictivity, not merely a reproducible delay.

## 6. Breathing-Stretching-Return-Phase null

**Prior observation.** Short-time collapse/reversal behavior could be reproduced substantially by a fixed-core null; observing a reversal was therefore not specific evidence for material-core feedback.

**v0.2.0 consequence.** S60 requires a material-over-fixed held-out advantage in addition to an absolute material predictive improvement.

## 7. Local Thread Texture numerical certification

**Prior observation.** Separate temporal refinement exposed clean near-fourth-order RK4 behavior in a related filament workbench, reinforcing that spatial and temporal convergence must not be conflated.

**v0.2.0 consequence.** S32 is a dedicated fixed-N timestep ladder, separate from S30 spatial resolution.

## 8. v0.1.1 Trefoil Dynamic Seed BASIC campaign

**Prior observation.** S30 qualified 12/12 and S35 qualified 8/8, producing a tight core-robust champion cluster. Yet all five long-run nominees stopped at `t ~= 0.768` from mesh quality before the return window at 0.8. The correct interpretation was RPO **not testable**, not “no RPO”.

**v0.2.0 consequence.** The five shapes are retained in `regression/v011_champions/` as numerical regression geometries. S40 carries explicit status/coverage fields and has separate `INDETERMINATE` verdicts when the RPO observation window or long-horizon coverage is insufficient.

## Imported ideas that are deliberately *not* treated as evidence

- projected Floquet stability is not full 3-D Euler stability;
- a low mesh-gauge sensitivity is numerical certification, not a new physical force;
- a measured propagation delay is not proof of feedback stabilization;
- a champion seed is a qualified start geometry within the searched family, not proof of a unique physical electron trefoil shape.
