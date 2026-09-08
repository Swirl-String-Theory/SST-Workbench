# Blind preregistration — v0.1.2

## Scope

v0.1.2 is a **phase-measurement and branch-identity discovery release**.  It does not confirm the historical `2.72 rad` target because the phase observable has changed.

## Unchanged symmetric closure null

\[
k_0L+m\Theta_B=2\pi n,
\]

with matched control

\[
k_\pm L+m\Theta_B=2\pi(n\pm\delta),
\qquad
g_{\rm sym}=\tfrac12[g(k_-)+g(k_+)].
\]

Only CLOSED/control pairs for which both eigenmodes pass convergence are eligible for growth comparison.

## Self-generated delay and phase

No delay is supplied.  The tracked dispersion branch gives

\[
v_g=\frac{d\omega}{dk},\qquad \tau_g=\frac{L}{|v_g|}.
\]

The wave packet independently supplies `tau_return_measured`.  Its envelope maximum is refined continuously.  Phase validity additionally requires the numerical uncertainty estimate to pass:

\[
\delta\phi=\sqrt{\delta\phi_t^2+\delta\phi_{\rm disp}^2}
\le \delta\phi_{\max}.
\]

Default discovery thresholds:

- local carrier phase step <= 0.05 rad;
- phase uncertainty <= 0.35 rad;
- return coherence >= 0.50.

A delay-valid but phase-invalid row may support the propagation-delay gate but **cannot** enter a phase-growth regression.

## Eigenbranch identity

Clock-focused presets enable overlap continuation from `U_s/V_theta = -1.0` to each target axial ratio.  A continuation that loses the preregistered minimum overlap is invalid rather than silently reselecting another eigenmode.

## Clock regimes

Before reveal:

\[
\texttt{FAST\_SWIRL\_LOCKED}:
0.60\le|\Im\lambda|/\Omega_{swirl}\le1.40,
\quad |v_g|\ge0.05,
\]

\[
\texttt{SLOW\_MODE}:
|\Im\lambda|/\Omega_{swirl}\le0.20,
\quad |v_g|\le0.05.
\]

Everything else is `OTHER_BRANCH`.

The primary `m=1` discovery is restricted to `FAST_SWIRL_LOCKED`.  This is a preregistered response to the clearly bimodal v0.1.1 audit; it is not chosen after seeing v0.1.2 growth outcomes.

## Stable growth response

The phase response is

\[
E_g=\frac{g_C-g_S}{|g_C|+|g_S|+2g_0}.
\]

Negative means exact CLOSED has lower positive growth.  Neutral/neutral pairs remain ties.

## m=1 discovery

`preset_swirl_clock_phase_discovery.json` has **no target phase**.  Reveal may estimate a circular minimum from phase-valid, both-valid, non-neutral, `FAST_SWIRL_LOCKED`, `m=1` rows after subtracting carrier-specific mean response.

It reports:

- pooled circular fit;
- discovered `phase_min_rad`;
- leave-one-carrier-out CV;
- carrier-grouped permutation p;
- carrier-bootstrap circular spread.

The result is explicitly `discovery_only`.  It cannot produce a confirmatory SST phase verdict.

## m=2 diagnostic

`preset_swirl_clock_m2_diagnostic.json` repeats the corrected phase measurement for `m=2` without importing any `m=1` target.  Its role is to determine whether phase structure is branch-specific or generic.

## Branch-map campaign

`preset_swirl_clock_branch_map.json` maps the same continued `m=1` branch across a denser axial-flow ladder and exports both lab-frame and intrinsic frequencies.  It is descriptive/discovery, not confirmatory.

## Phase-resolution stress campaign

`preset_phase_resolution_stress.json` tightens:

- radial ladder to 32/48/64;
- phase step to 0.025 rad;
- phase uncertainty to 0.20 rad;
- dispersion residual/branch overlap thresholds.

A phase relation that disappears under this stress test is not numerically certified.

## Confirmation rule

A new phase found by v0.1.2 must be frozen in a **later independent release** and tested on carriers/data not used to choose it.  v0.1.2 itself cannot promote discovery to confirmation.
