# Methodology — Dimensionless Dynamic Ratio Harness

## 1. Epistemic mode

This package operates in the CANON v0.8.34 **symbolic/prediction-preparation mode**:

- dimensional primitives are removed;
- outputs are dimensionless ratios and convergence diagnostics;
- no measured target is used to set a model parameter;
- no particle interpretation is attached before the numerical dynamics passes its own gates.

## 2. Comparison ensemble

Default protocol:

\[
\Gamma=1,
\qquad
L=2\pi,
\qquad
\epsilon=\text{fixed},
\qquad
\rho=1\ \text{in the energy proxy}.
\]

Fixing total centerline length and core radius also fixes the simple tube-volume proxy:

\[
V_{\rm tube}^{*}
=\pi\epsilon^2L.
\]

This is a deliberately austere comparison ensemble. Other protocols are allowed only as separately preregistered campaigns.

## 3. Curve sources

The code supports:

- Brian Gilbert ideal-knot `AB` Fourier blocks;
- a circular ring;
- fallback analytic trefoil and figure-eight parametrizations.

The default campaign uses the `AB` source for:

- `0:1:1` ring;
- `3:1:1` trefoil;
- mirrored `3:1:1`;
- `4:1:1` figure-eight.

The label `ideal` is treated as source metadata, not as proof of dynamical stability or global ropelength minimality.

## 4. Arclength resampling

All curves are periodically resampled to a uniform piecewise-linear arclength mesh before evaluation and after each evolution step.

The remeshing is a numerical gauge choice. A valid result must be stable when the remeshing frequency and point count are varied.

## 5. Regularized Biot--Savart velocity

For vertices \(\mathbf X_i\) and segment midpoints \(\mathbf m_j\):

\[
\mathbf u_i
=
\frac{\Gamma}{4\pi}
\sum_j
\Delta\mathbf X_j
\times
(\mathbf X_i-\mathbf m_j)
\,K_\epsilon(|\mathbf X_i-\mathbf m_j|).
\]

Implemented kernels:

### Rosenhead

\[
K_\epsilon(r)
=
(r^2+\epsilon^2)^{-3/2}.
\]

### Rankine cutoff

\[
K_\epsilon(r)
=
\max(r^2,\epsilon^2)^{-3/2}.
\]

### Winckelmans--Leonard

\[
K_\epsilon(r)
=
\frac{r^2+(5/2)\epsilon^2}
{(r^2+\epsilon^2)^{5/2}}.
\]

A ratio that changes qualitatively across these admissible kernels is not yet regulator-robust.

## 6. Tangential gauge

Tangential velocity changes parametrization but not the geometric centerline. Shape evolution may therefore use:

\[
\mathbf u_\perp
=
\mathbf u-(\mathbf u\cdot\mathbf t)\mathbf t.
\]

Rigid translation and rotation are retained.

## 7. Relative-motion solve

The code solves a linear least-squares problem for:

\[
\mathbf U,
\qquad
\boldsymbol\Omega,
\]

in:

\[
P_i\mathbf u_i
\approx
P_i\left[
\mathbf U+
\boldsymbol\Omega\times(\mathbf X_i-\mathbf X_c)
\right].
\]

The residual is normalized by the projected velocity norm. This identifies whether a static centerline is approximately a translating/rotating relative state under the selected discretized operator.

## 8. Energy proxy

The code uses:

\[
E_\epsilon
=
\frac{\Gamma^2}{8\pi}
\sum_{ij}
\frac{
\Delta\mathbf X_i\cdot\Delta\mathbf X_j
}
{
\sqrt{|\mathbf m_i-\mathbf m_j|^2+\epsilon^2}
}.
\]

This is a regularized line-energy proxy. It is not a complete finite-core kinetic-energy integral with a resolved internal vorticity profile.

## 9. Sampled reach

The diagnostic reach is the minimum of:

- local curvature radius;
- half a sampled approximately doubly-critical chord.

A chord candidate must be approximately perpendicular to tangents at both endpoints. This is materially better than a raw nearest-point distance, but it remains weaker than a certified continuous dcsd/reach solver.

## 10. Evolution

The first implementation uses explicit RK4 with periodic remeshing. It records:

- length drift;
- energy-proxy drift;
- curvature coefficient of variation;
- rigid rate;
- deformation rate;
- recurrence error.

The short quick campaign is a smoke test, not a long-time stability proof.

## 11. Recurrence quotient

For each sampled time, the code minimizes RMSD over:

- translation by centering;
- proper rotation via Kabsch alignment;
- cyclic index shift.

It does not permit a reflection in the default recurrence test. A mirror trefoil is a separate preregistered state.

## 12. Ratio policy

Ratios use the ring as an internal reference under the same protocol. A ratio is only meaningful if the denominator is nonzero and converged.

Primary outputs:

\[
\mathcal R_E,
\quad
\mathcal R_{\rm rigid},
\quad
\mathcal R_{\rm def},
\quad
\mathcal R_I,
\quad
\mathcal R_B.
\]

A dominant shape-frequency ratio is reported only when both time series contain a resolvable nonzero spectral peak.

## 13. Promotion ladder

- **Level 0:** smoke test;
- **Level 1:** resolution convergence;
- **Level 2:** two-kernel robustness;
- **Level 3:** small-residual relative state;
- **Level 4:** periodic-orbit solve;
- **Level 5:** Floquet stability;
- **Level 6:** independent external benchmark;
- **Level 7:** only then discuss particle mapping.
