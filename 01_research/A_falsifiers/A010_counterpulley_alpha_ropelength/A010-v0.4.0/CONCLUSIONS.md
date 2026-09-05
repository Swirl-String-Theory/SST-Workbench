# CONCLUSIONS -- v0.4.0

## Status

**[DERIVED NEGATIVE, bounded search domain]** No accepted relative periodic orbit was found in the preregistered v0.4 seed/time window. Therefore no true Floquet multiplier or alpha-comparison claim is permitted.

## What changed relative to v0.3

v0.3 established that a frozen temporal Kelvin eigenspectrum can produce a genuinely dynamical phase, but the base `+Gamma/-Gamma` pair was not a relative equilibrium. v0.4 removes that logical loophole by making the orbit itself the first gate.

The primary condition is now

\[
\mathbf X(T)=g\mathbf X(0)+\mathcal O(\varepsilon_{\rm RPO}),
\qquad g\in SE(3),
\]

modulo one common cyclic filament relabelling.

Only after this condition holds may the code evaluate

\[
\mathbf M=D(g^{-1}\circ\phi_T).
\]

## Full native reference campaign

All implementation/numerical prerequisites H0--H5 pass.

The canonical seed gives

\[
\varepsilon_{\rm RPO}=0.7019663968,
\qquad
\varepsilon_f=1.2224030728,
\]

at its best eligible snapshot \(\hat T=0.21\). It is not an RPO.

The best of 36 preregistered seeds is

\[
(a/D,\epsilon/D,\phi)=(0.30,0.10,\pi/2),
\]

with

\[
\varepsilon_{\rm RPO}=0.4090414924,
\qquad
\varepsilon_f=0.5595702741.
\]

This is an improvement over the canonical seed, but still much too large to identify a relative periodic orbit.

## Important numerical correction

Raw Lagrangian filament markers showed strong tangential clustering. v0.4 therefore evolves the embedded curve in normal-flow gauge,

\[
\mathbf u_\perp=\mathbf u-(\mathbf u\cdot\mathbf t)\mathbf t.
\]

This removes a pure reparametrisation direction while preserving the geometric centerline motion. After this correction, native/Python parity remains at machine precision and RK4 convergence is clean. The negative RPO result therefore no longer depends on marker clustering.

## Consequence for alpha

The alpha benchmark remains closed in the bundled reference runs. This is deliberate: a number produced from the v0.3 frozen spectrum is not promoted to a true Floquet phase until an actual periodic/relative-periodic base trajectory exists.

## Falsifiable next step

The correct v0.4.1/v0.5 search direction is **RPO shooting/continuation**, not alpha fitting:

1. extend the blind seed coordinates (relative longitudinal phase, core closure, circulation ratio only if physically preregistered);
2. minimize the recurrence residual with Newton--Krylov or multiple shooting;
3. demand resolution and finite-core convergence of the orbit itself;
4. only then compute `D(g^-1 o phi_T)` and its multiplier spectrum;
5. unblind alpha only after the monodromy gates pass.

A successful RPO would be a new dynamical object independently of alpha. Failure of a substantially enlarged preregistered orbit search would instead falsify this specific two-channel counter-pulley realization more strongly.
