# VortexLab v7.6.25 — continuous DCSD/reach solver

Base: `v7.6.24f3`

## Scope

This release implements roadmap item v7.6.25 as a passive geometry audit. It does not alter Biot–Savart, RK4, topology clearance, `a_sim`, `R_horn`, the legacy reach estimate, or any Swirl-Clock transfer law.

## New continuous reach solver

For every closed component, the audit separately computes:

- continuous curvature limit `a_kappa = 1 / kappa_max`;
- continuous doubly-critical self distance `a_self = d_DCSD / 2`;
- continuous inter-component limit `a_inter = d_inter / 2`;
- final geometric reach `min(a_kappa, a_self, a_inter)`;
- dominant limiter: `CURVATURE`, `SELF_DCSD`, `INTER_COMPONENT`, or `TIE`;
- stationary-point parameters, points, Hessian diagnostics, and tangent-orthogonality residuals.

The DCSD conditions are solved as

```text
(r(s) - r(t)) · r'(s) = 0
(r(s) - r(t)) · r'(t) = 0
```

using broad deterministic seed selection followed by damped Newton refinement with periodic parameter wrapping.

## Curve representation

- Fourier, ideal, and KnotPlot catalog curves are evaluated from their analytic Fourier series.
- Arbitrary sampled curves use a periodic C² cubic spline in chord-length parameter.
- An explicit sampled-circle spline gate verifies convergence of the spline path independently from the exact analytic circle gate.

## Reach audit runner

A new locked workflow step appears after the continuum audit:

```text
SPEC → decomposition → holdouts → continuum → continuous reach/DCSD
```

The reach runner provides three profiles:

- Quick: `N = 128, 256, 512`
- Standard: `N = 128, 192, 256, 384, 512, 768`
- Confirmatory: `N = 256, 384, 512, 768, 1024, 1536`

It always includes exact analytic anchors and adds the currently selected Ideal, Fseries, and KnotPlot geometries.

## Engine gates

- `G0`: exact unit-circle reach
- `G0b`: sampled periodic C²-spline circle convergence
- `G1`: rigid-transform invariance
- `G2`: known two-component inter-distance anchor
- `G3`: DCSD tangent-orthogonality closure
- `G4`: Gilbert `D` versus continuous DCSD diameter
- `G5`: last-pair resolution convergence and limiter stability

## Source-precision audit

Gilbert `D = 1` is checked against the continuous DCSD branch. Several rounded high-order Fourier series reproduce `d_DCSD / 2 ≈ 0.5` accurately while their analytic second derivatives yield a smaller curvature radius. This is reported separately as:

```text
R41 · ideal coefficient precision / curvature consistency
```

The discrepancy is not hidden by widening tolerances and does not modify the source data.

## Exports

The runner exports TXT and JSON using schema:

```text
vortexlab-continuous-reach-audit/1.0
```

Reports contain the full solver provenance, all per-resolution results, convergence rows, limiter identities, and gate decisions.

## Deliberately unchanged

Byte-identical to v7.6.24f3:

- `velocityCore`
- `velAll`
- `rk4Step`
- `topologyClearance`
- `intrinsicCoreRadiusLimit`
- `approximateDoublyCriticalDistance`

The existing approximate reach remains visible as a legacy diagnostic. The new continuous result is not fed back into the dynamics.

## Validation boundary

- Inline JavaScript syntax: PASS
- Static DOM IDs: unique
- Pure reach-kernel Node harness: PASS for exact circle, spline circle, and a two-component known-gap anchor
- Solver-function invariance: PASS
- Full interactive WebGL/browser run: not completed; headless Chromium hung before DOM export
