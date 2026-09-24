# Geometry qualification and convergence

## Reconstruction

Each closed polygonal carrier is cleaned only for exact/near-exact duplicate closure points and degenerate consecutive edges. It is then reconstructed with a periodic cubic spline. The native source polygon is not overwritten.

The default cross-source normalization is

\[
\widehat C = \frac{C-\langle C\rangle}{L(C)}
\]

so the total length is one. `scale_context` records native component lengths, native total length and the applied scale factor.

## Local observables

For a regular curve \(\mathbf r(u)\),

\[
\kappa = \frac{\|\mathbf r'\times\mathbf r''\|}{\|\mathbf r'\|^3},
\qquad
\tau = \frac{(\mathbf r'\times\mathbf r'')\cdot\mathbf r'''}{\|\mathbf r'\times\mathbf r''\|^2}.
\]

The builder stores max/RMS/std curvature and RMS torsion at every resolution.

## Writhe and ACN

`Wr` and `ACN` are evaluated by midpoint quadrature of the Gauss double integral over the sampled polygonal centerline. Adjacent segments are excluded in the self-integral. The C++ backend parallelizes the \(O(N^2)\) sum.

## Clearance, doubly-critical distance and thickness

`d_min` is a nonlocal segment-segment clearance diagnostic. It is not substituted for the doubly-critical distance.

For the reconstructed smooth curve the numerical **reach radius** target is

\[
\operatorname{reach}(C)
=
\min\left(\frac{1}{\kappa_{\max}},\frac{d_{\rm dc}}{2}\right).
\]

PKLSA additionally preserves the historical diameter convention

\[
\operatorname{Thi}(C)=2\,\operatorname{reach}(C),
\qquad
\operatorname{Rop}=\frac{L}{\operatorname{Thi}}.
\]

This makes `Rop` directly comparable to the Gilbert/KnotPlot `D=1` trefoil scale around 16.37. The builder also emits `ropelength_reach=L/reach`, which is twice the diameter-convention value and is useful when comparing literature that defines thickness as a tube radius.

Links add the usual half inter-component separation constraint to `reach`. `d_dc` is estimated by resolution-refined chord candidates satisfying endpoint tangent-orthogonality tolerances. This is a numerical estimator, not an exact symbolic certificate. The estimator must converge before `Thi`, `reach` or either ropelength convention can be marked `RESOLVED`.

## Convergence semantics

For successive values \(Q_N\), the builder evaluates relative changes. Default extended thresholds are:

- `RESOLVED`: finest relative change \(\le 5\times10^{-3}\) and preceding behavior is compatible;
- `CONVERGING`: finest change \(\le 5\times10^{-2}\) with non-divergent trend;
- `COARSE`: insufficient ladder depth or only weak evidence;
- `UNRESOLVED`: missing/unstable/non-convergent result;
- `REFERENCE_VALUE`: source-provided value, stored outside the numerical ladder.

No result becomes `REFERENCE_VALUE` merely because its source is prestigious.
