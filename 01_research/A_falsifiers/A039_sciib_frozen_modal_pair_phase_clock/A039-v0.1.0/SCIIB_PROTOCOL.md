# SC-IIb Frozen Modal-Pair / Subspace Phase Clock Protocol v0.1.0

## Hypothesis

SC-IIb is deliberately distinct from both earlier hypotheses:

- **SC-I:** the complete centerline returns after a period;
- **SC-II:** one frozen scalar POD coordinate has a persistent Hilbert phase;
- **SC-IIb:** a discovery-frozen **two-dimensional modal subspace** supports a
  directed, predictive rotation even if neither scalar coordinate is a good
  clock by itself.

For a frozen POD pair \((\Phi_i,\Phi_j)\), the natural response is projected to

\[
 a_i(t)=\langle X(t)-\bar X_D,\Phi_i\rangle,
 \qquad
 a_j(t)=\langle X(t)-\bar X_D,\Phi_j\rangle .
\]

Only a constant modal-pair center estimated in the discovery window is removed;
**no holdout detrending and no extrapolated discovery slope are allowed.**  The
orientation is fixed from the sign of discovery-window modal angular momentum.
The clock phase is

\[
 \phi_{ij}(t)=\operatorname{unwrap}\operatorname{atan2}(a_j(t),a_i(t)),
 \qquad
 L_{ij}=a_i\dot a_j-a_j\dot a_i .
\]

A full-shape return is not required.

## Blindness and discovery/holdout separation

1. Source identity is hidden exactly as in the v0.2.2.x provenance pipeline.
2. The POD basis is learned only on the absolute discovery interval.
3. Pair eligibility is decided only from discovery data.
4. The same frozen pair, center, ordering/orientation and thresholds are used on
   the holdout and on low/high mesh-gauge replays.
5. The holdout may reject a pair but may never select a new pair.
6. Only the **natural** channel can become a primary SC-IIb candidate.  The odd
   ±probe channel is a diagnostic/null control.

## Q1 — discovery-frozen pair eligibility

BASIC preregistration:

- combined discovery energy >= 0.05;
- weaker/stronger mode energy ratio >= 0.35;
- pair circularity
  \(C=2\sqrt{E_iE_j}/(E_i+E_j)\ge0.80\);
- relative discovery frequency split <= 0.20;
- analytic cross-phase PLV >= 0.60;
- distance from ±quadrature <= 0.55 rad;
- dominant discovery angular-momentum sign fraction >= 0.80.

These gates prevent arbitrary pairs of unrelated POD modes from being promoted
because their holdout happens to look rotational.

## Q2 — directed multi-wrap rotation

On the untouched holdout:

- >= 4 net phase wraps;
- fraction of positive phase increments >= 0.90;
- fraction with positive modal angular momentum >= 0.90.

The sign convention itself is frozen from discovery.

## Q3 — frequency coherence

- \(R^2[\phi(t)\sim\Omega t+\phi_0]\ge0.90\);
- cycle-period CV <= 0.15;
- instantaneous angular-velocity CV <= 0.50 on reliable-radius samples.

## Q4 — phase/radius stability

- one-cycle residual phase diffusion RMS <= 0.75 rad;
- pair-radius CV <= 0.60;
- final/initial radius retention in [0.40, 2.50];
- >=95% of samples have radius >=25% of the median radius.

This rejects apparent winding produced by repeated passages near the origin,
where atan2 phase is physically ill-conditioned.

## Q5 — out-of-sample phase prediction

The first 40% of the holdout calibrates a constant angular velocity.  Without
refitting, the remaining holdout must satisfy:

- phase prediction RMS <= 1.00 rad;
- terminal phase error <= 1.57 rad.

## Q6 — basis-gauge invariance

A two-dimensional POD eigenspace has no unique coordinate axes.  SC-IIb therefore
repeats the phase calculation after deterministic orthogonal rotations, sign
flips and mode swaps within the same frozen subspace.  After orientation
canonicalization:

- relative frequency spread <= 1e-6;
- relative period spread <= 1e-6;
- relative phase-diffusion spread <= 1e-5.

This is an implementation-level gauge audit of the claim that the measured
clock belongs to the subspace rather than to an arbitrary POD-axis convention.

## Q7 — natural channel

Primary candidate status requires `channel == natural`.  Odd/probe pairs can be
reported but cannot satisfy Q7.

## Provisional candidate

A candidate requires Q1..Q7 simultaneously and a geometry-certified parent
carrier.  Geometry gates are inherited unchanged from the certified v0.2.2.x
infrastructure.

## Mesh-gauge certification

Only provisional carriers are replayed.  The same frozen baseline pair is used.
Both low and high mesh-gauge trajectories must independently satisfy the
holdout phase gates, plus:

- relative period spread <= 0.15;
- relative angular-frequency spread <= 0.15;
- relative phase-diffusion spread <= 0.50.

## Provenance robustness

Source-family voting is unchanged: multiple Fremlin variants are multiple
shapes but one independent provenance family.  BASIC requires at least two
source families and a source-family candidate fraction >=2/3 with period spread
<=0.30.

## Stage B mechanism test

Existence and mechanism remain separate hypotheses.  For a certified pair,
segment stretch is projected onto the two frozen mode-strain fields.  The
instantaneous **phase-tangent** stretch observable is

\[
 \sigma_{\rm tan}(t)=
 -\sin\phi(t)\,\sigma_i(t)+\cos\phi(t)\,\sigma_j(t).
\]

The material-core branch tests a discovery-selected delay from
\(\sigma_{\rm tan}\) to residual phase velocity \(\delta\dot\phi\), then checks
that correlation on holdout and against phase-shift nulls.  A fixed-core branch
is the mechanism null.  A phase-clock PASS does not imply a Stage-B mechanism
PASS.

## Global failure / indeterminate policy

The inherited coverage rule is retained.  Absence of candidates can become a
global FAIL only when the preregistered geometry-valid coverage requirement is
met.  Otherwise the result is
`INDETERMINATE_SCIIB_INSUFFICIENT_VALID_COVERAGE`.

## Scope

The dynamics remain a regularized finite-core vortex-filament/Biot-Savart
proxy, not a proof about a full volumetric 3-D Euler solution.
