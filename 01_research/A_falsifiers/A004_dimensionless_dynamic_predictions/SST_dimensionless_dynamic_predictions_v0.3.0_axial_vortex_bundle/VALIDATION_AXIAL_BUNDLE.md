# VALIDATION — v0.3.0 axial vortex bundle

## Build scope

Validated components:

- finite-radius continuum Rankine bundle;
- frozen infinite discrete axial tubes;
- physical-tube interpretation;
- numerical-discretization interpretation;
- hole-derived bundle radius;
- circulation-phase clock diagnostics;
- B0–B8 configuration ladder;
- paired continuum/discretization analyzer.

Not validated:

- full three-dimensional bending and mutual evolution of the background tubes;
- reconnection or Kelvin waves;
- finite-core Euler existence or KAM stability;
- identification of the clock phase with physical proper time.

## Automated tests

\[
\boxed{11/11\ \mathrm{unit\ tests\ passed}}
\]

The tests cover ring controls, mirror parity, self-induction kernels, solid-body invariance, physical flux scaling, fixed-total discretization, Rankine inside/outside behavior and the clock-rate identity.

## Physical-tube smoke test

Protocol: trefoil, resolution 96, fixed sampled reach, \(\epsilon=0.05\), Rankine tube cores,

\[
R_{\rm bundle}=R_{\rm hole}^{\rm free},
\qquad
|\Gamma_{\rm tube}|=0.25.
\]

| sign | \(N\) | \(\Gamma_{\rm hole}\) | intrinsic residual | residual reduction |
|---:|---:|---:|---:|---:|
| − | 19 | −4.75 | 1.135831815 | −4.150268 |
| − | 7 | −1.75 | 0.479072701 | −1.172287 |
| − | 1 | −0.25 | 0.233787205 | −0.060075 |
| + | 1 | 0.25 | 0.221892984 | −0.006142 |
| + | 7 | 1.75 | 0.437080659 | −0.981880 |
| + | 19 | 4.75 | 1.089205698 | −3.938849 |

The isolated baseline is approximately

\[
\epsilon_{\rm int}^{(0)}=0.220538375.
\]

Increasing \(N\) at fixed tube circulation increases total flux and strongly increases the deformation residual. No smoke-test case passes the 5% equilibrium gate.

## Numerical-discretization smoke test

Here

\[
|\Gamma_{\rm hole}|=1,
\qquad
\Gamma_{\rm tube}=\Gamma_{\rm hole}/N.
\]

| sign | \(N\) | intrinsic residual | continuum field error | continuum residual error |
|---:|---:|---:|---:|---:|
| − | 1 | 0.335299753 | 0 | 0 |
| − | 7 | 0.335274001 | 0.000334538 | 0.000076804 |
| − | 19 | 0.335085856 | 0.000368398 | 0.000637927 |
| − | 37 | 0.335167664 | 0.000222937 | 0.000393944 |
| − | 61 | 0.335194449 | 0.000176325 | 0.000314059 |
| + | 1 | 0.301240903 | 0 | 0 |
| + | 7 | 0.300707734 | 0.000334538 | 0.00176991 |
| + | 19 | 0.300734947 | 0.000368398 | 0.00167957 |
| + | 37 | 0.300932819 | 0.000222937 | 0.00102272 |
| + | 61 | 0.300996247 | 0.000176325 | 0.000812163 |

At \(N=61\), averaged over both circulation signs:

\[
\delta u_{\rm rms}=0.000176325,
\qquad
\delta\epsilon_{\rm int}=0.000563111.
\]

The clock-rate error is exactly zero because total circulation and radius are held fixed by construction.

## Continuum stabilization scan

A 98-row exploratory scan varied

\[
\frac{R_{\rm bundle}}{R_{\rm hole}^{\rm free}}
\in
\{0.25,0.5,0.75,1,1.25,1.5,2\}
\]

and signed total circulation up to magnitude 4.

The best case was

\[
\frac{R_{\rm bundle}}{R_{\rm hole}^{\rm free}}=2.0,
\qquad
\Gamma_{\rm hole}=-0.25,
\]

with

\[
\epsilon_{\rm int}=0.219211249,
\qquad
\mathrm{reduction}=0.602\%.
\]

This is only a sub-percent improvement and remains far above the preregistered 5% gate.

## Validation verdict

```text
PHYSICAL-TUBE-FLUX-SCALING-PASS
NUMERICAL-DISCRETIZATION-CONVERGENCE-PASS
CLOCK-RATE-CONSISTENCY-PASS
FROZEN-HOLE-BUNDLE-STABILIZATION-FAIL
FULL-3D-BACKREACTION-OPEN
```
