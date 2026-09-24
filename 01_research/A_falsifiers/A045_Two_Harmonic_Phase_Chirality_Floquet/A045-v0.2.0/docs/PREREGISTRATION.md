# Preregistration — v0.2.1

The v0.2.1 execution patch does not alter the preregistered scientific protocol, blind salts, gates, thresholds, seeds, or condition grid from v0.2.0.

## Question
Does the exact threefold dynamical symmetry of the counter-rotating two-colour drive survive a regularized nonlocal finite-core filament evolution, across a frozen ensemble of independently qualified trefoil candidates and a preregistered core/mesh ladder?

## Primary identity
For the counter-rotating drive,

\[
A\!\left(t+\frac{T}{3}\right)=R_z\!\left(\frac{2\pi}{3}\right)A(t)R_z^{-1}\!\left(\frac{2\pi}{3}\right).
\]

The co-rotating arm is the positive control that generally lacks this identity.

## Blind gates
- G0 source-leakage audit has zero forbidden SST-calibration tokens outside the audit implementation itself.
- G1 frozen input hashes match exactly.
- G2 one anonymous drive class has the analytic C3 identity.
- G3 one anonymous numerical branch satisfies the finite-core equivariance threshold.
- G4 the control branch is separated by the preregistered ratio.
- G5 temporal half-step refinement remains below threshold.
- G6 short-horizon length drift remains bounded.
- G7 point-spacing coefficient of variation remains bounded.

The scoring code uses anonymous IDs. Seed labels, arm labels, phase indices and core settings are written to `private_reveal/reveal_map.json` only after blind metric generation.

## Scope guard
This release tests finite-core numerical equivariance and seed robustness. It does not establish a material analogy, an SST particle mechanism, or Floquet stability. Formal multipliers require a separately certified periodic or relative-periodic orbit.
