# SC-III pre-registered protocol v0.1.0

## Observable construction

1. Accept only carriers that already pass the unchanged Stage-A geometry certification.
2. Learn the POD observable basis only on the absolute discovery window (`sciii_discovery_time=4.0`).
3. Fit a linear DMD map on discovery POD coordinates.
4. Enumerate positive-frequency complex eigenmodes. No holdout sample participates in discovery ranking.
5. Freeze the discovery complex eigenmode as the reference branch.

## Q1 — discovery complex Koopman mode

A candidate must have:
- coordinate energy fraction >= 0.03;
- |growth rate| / angular frequency <= 0.20;
- one-step complex eigen-relation residual <= 0.40;
- >= 0.60 discovery cycles.

## Moving-subspace continuation

Holdout windows have fixed width 2 discovery periods (minimum 40 samples) and 35% step. In each window the local positive-frequency DMD mode is matched to the preceding mode using complex-mode overlap penalized by frequency jump. Arbitrary local complex phase is removed by parallel transport before interpolation.

## Q2 — continuation
- matched-window fraction >= 0.75;
- median complex-mode overlap >= 0.65;
- minimum overlap >= 0.35;
- local frequency CV <= 0.25.

## Q3 — clock phase
- >= 4 wraps;
- monotone phase fraction >= 0.90;
- global phase-linearity R² >= 0.90;
- cycle-period CV <= 0.15;
- one-cycle phase diffusion <= 0.75 rad.

## Q4 — persistent/near-neutral coordinate
- radius CV <= 0.60;
- terminal/initial radius ratio in [0.40, 2.50];
- reliable-radius fraction >= 0.80;
- median local |growth|/omega <= 0.25.

## Q5 — local out-of-sample prediction
Within each matched window, the local eigenvalue predicts the later phase. Median RMS phase error must be <= 1.00 rad and median terminal error <= 1.57 rad.

## Q6 — intrinsic channel
Only the natural channel can create a primary SC-III candidate. Odd/probe results are null diagnostics.

## Certification
A provisional candidate is replayed with low/high tangential mesh redistribution. Period/frequency spreads must each be <= 0.15. Source-family provenance is then evaluated with equal family votes. Stage B is run only on certified candidates.

## Stage B
The discovery complex right DMD mode is mapped back into spatial geometry; its real/imaginary strain weights define the tangent stretch observable. Material-core delayed stretch→phase-rate coupling is compared with the fixed-core null. Clock existence does not imply the mechanism claim.
