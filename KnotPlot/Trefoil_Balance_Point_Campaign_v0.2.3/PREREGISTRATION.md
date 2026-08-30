# Trefoil Balance Point Campaign v0.2.3 — preregistration

## Question

Does the expansion/contraction zero that is still moving at 100k settle by 200k,
or does it approach/leave the frozen q/h/p panel?

## Frozen panel

All 20 Q01..Q20 q/h/p settings are copied exactly from v0.2.2.
No settings are added or removed.

Current panel:
- t_min = 1.215
- t_max = 1.32

Observed 100k zero:
- t* = 1.292108327285

## Continuation

Resume all 20 states from i100000.k to:
120k, 140k, 160k, 180k, 200k.

No fitto, refine, or centre is permitted after checkpoint load and before the
first resumed ago. A 100k L/Rg reload continuity probe must pass first.

## Settlement gates

Inherited from v0.2.2:
- |dt*/di| <= 0.0010 t per 10k
- last-three t* spread <= 0.0025

Boundary sentinel:
- if the last tracked zero lies within 0.005 of t_min or t_max:
  `ZERO_AT_FROZEN_RANGE_BOUNDARY`
- if the crossing disappears and both panel endpoint E values indicate escape:
  `ZERO_LEFT_FROZEN_PANEL`

## Stronger geometric diagnostic

At every zero crossing, ΔL/L0 and ΔRg/Rg0 are separately interpolated at the
same crossing fraction.

A `TRUE_GEOMETRIC_FIXED_POINT_CANDIDATE` requires:
1. the zero-track settlement gates above;
2. |slope(ΔL/L0 at zero)| <= 7.5e-4 per 10k;
3. |slope(ΔRg/Rg0 at zero)| <= 7.5e-4 per 10k.

If the zero settles but either separate observable still drifts, classification:
`SETTLED_COMPENSATING_BALANCE_ZERO`.

## Planning forecast only

The observed 30k..100k zero increments were used only to choose the next horizon,
not as an acceptance fit.

Geometric-decrement forecast:
- t*(200k) ≈ 1.313835
- t*(400k) ≈ 1.334608

Power-law decrement forecast:
- t*(200k) ≈ 1.317070
- t*(400k) ≈ 1.356833

Since t_max=1.320, 400k is not preregistered in this release.
