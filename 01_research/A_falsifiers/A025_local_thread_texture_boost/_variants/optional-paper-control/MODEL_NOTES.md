# Model notes — v0.3.0

## 1. Scope

The workbench tests a local SST background made of explicit closed vortex filaments.  It does not assume that a globally uniform absolute translational velocity is observable.

The background may possess an objective local texture: thread orientation, density, circulation and spatial gradients.

## 2. Exact regularized straight-segment kernel

For one straight filament segment parameterized by arclength \(l\),

\[
\mathbf q(l)=\mathbf p_0+l\mathbf e,\qquad 0\le l\le L,
\]

v0.3 evaluates the Rosenhead-regularized line integral

\[
\mathbf v(\mathbf x)=
\frac{\Gamma}{4\pi}
\int_0^L
\frac{\mathbf e\times[\mathbf x-\mathbf q(l)]}
{\left(|\mathbf x-\mathbf q(l)|^2+a^2\right)^{3/2}}\,dl.
\]

Let

\[
z_0=\mathbf e\cdot(\mathbf x-\mathbf p_0),
\qquad
\mathbf r_\perp=(\mathbf x-\mathbf p_0)-z_0\mathbf e,
\qquad
A=|\mathbf r_\perp|^2+a^2,
\]

and \(z_1=z_0-L\).  Because \(\mathbf e\times\mathbf r_\perp\) is constant along the segment,

\[
\boxed{
\mathbf v_{\rm seg}=
\frac{\Gamma}{4\pi}
(\mathbf e\times\mathbf r_\perp)
\left[
\frac{z_0}{A\sqrt{A+z_0^2}}
-
\frac{z_1}{A\sqrt{A+z_1^2}}
\right].
}
\]

For a short segment \(L\ll |\mathbf r|\), the leading term reduces to the familiar midpoint form

\[
\mathbf v_{\rm seg}\sim
\frac{\Gamma}{4\pi}
\frac{\Delta\boldsymbol\ell\times\mathbf r}
{(|\mathbf r|^2+a^2)^{3/2}},
\]

so the v0.2 kernel is recovered as the small-segment limit.

Dimensional check:

\[
[\Gamma]=L^2T^{-1},\qquad
[\mathbf v_{\rm seg}]=LT^{-1}.
\]

## 3. RK4 and common boost covariance

The knot/link evolves under

\[
\frac{d\mathbf X}{dt}=\mathbf F(\mathbf X,t)
=\mathbf v_{\rm self}[\mathbf X]
+\mathbf v_{\rm threads}(\mathbf X,t)
+\mathbf U_0.
\]

For the common-boost case the complete frozen substrate translates as

\[
\mathbf T_a(t)=\mathbf T_a(0)+\mathbf U_0t.
\]

The four RK4 stages are

\[
\mathbf k_1=\mathbf F(\mathbf X_n,t_n),
\]

\[
\mathbf k_2=\mathbf F\!\left(\mathbf X_n+\frac{\Delta t}{2}\mathbf k_1,t_n+\frac{\Delta t}{2}\right),
\]

\[
\mathbf k_3=\mathbf F\!\left(\mathbf X_n+\frac{\Delta t}{2}\mathbf k_2,t_n+\frac{\Delta t}{2}\right),
\]

\[
\mathbf k_4=\mathbf F(\mathbf X_n+\Delta t\mathbf k_3,t_n+\Delta t),
\]

\[
\mathbf X_{n+1}=\mathbf X_n+
\frac{\Delta t}{6}(\mathbf k_1+2\mathbf k_2+2\mathbf k_3+\mathbf k_4).
\]

## 4. Constant final time and subcycling

A campaign freezes

\[
T_{\rm final}=f_T\frac{R_{g,\rm ref}}{U_g},
\qquad
U_g=\frac{|\Gamma|}{4\pi R_{g,\rm ref}}.
\]

For a characteristic segment spacing \(\Delta s\), the certification scheduler defines

\[
\Delta t_{\rm ds^2}=C_{\Delta s^2}\frac{\Delta s^2}{|\Gamma|}.
\]

If the nominal outer step is larger, it is subdivided.  The implemented step is always chosen so that an integer number of substeps exactly spans the outer step and therefore exactly preserves \(T_{\rm final}\).

## 5. Arclength redistribution

After a complete outer RK4 step, the polygonal curve may be resampled to uniform arclength with the same bead count.  This changes the discrete parametrization, not the continuous target curve.  Because the interpolation is not mathematically exact, its residual influence is treated as a numerical issue and is expected to vanish under spatial convergence.

## 6. Closed thread topology

Every background component is a closed polygonal curve

\[
C_a:S^1\rightarrow\mathbb R^3,
\]

so no discrete vortex filament terminates.  This is the filament-level counterpart of

\[
\nabla\cdot\boldsymbol\omega=0.
\]

The finite-difference `div(curl(v))` calculation remains a numerical implementation diagnostic; topological closure is the stronger structural condition.

## 7. Core-clearance admissibility

The code measures

\[
d_{\min}=\min d(C_{\rm knot},C_{\rm thread})
\]

and reports

\[
\chi_{\rm clear}=\frac{d_{\min}}{a_{\rm knot}+a_{\rm thread}}.
\]

If \(\chi_{\rm clear}<1\), the finite cores geometrically overlap.  v0.3 does not silently call the resulting dynamical response evidence; its bridge status becomes `INDETERMINATE` unless the configured clearance condition is satisfied.

## 8. Two density mechanisms

### Circulation texture

At fixed thread positions,

\[
\Gamma_a=\Gamma_0 w_a,
\qquad
\langle w_a\rangle=1.
\]

### Position/number-density texture

At fixed \(\Gamma_a=\Gamma_0\), lattice coordinates along a hidden gradient direction are transformed locally as

\[
x'=x-\frac{g}{2R}x^2,
\]

with Jacobian

\[
\frac{dx'}{dx}=1-g\frac{x}{R}.
\]

Thus the local areal spacing changes while total thread count and per-thread circulation remain fixed.

The two cases are intentionally not identified with one another.

## 9. Finite-source radial limit

For a hidden source center \(\mathbf X_s\), each local thread anchor \(\mathbf q_a\) receives the radial direction

\[
\mathbf n_a=\frac{\mathbf q_a-\mathbf X_s}{|\mathbf q_a-\mathbf X_s|}.
\]

As

\[
D=|\mathbf x_c-\mathbf X_s|\rightarrow\infty,
\]

all \(\mathbf n_a\) must converge to the common local direction \(\mathbf n_0\).  v0.3 tests both the initial background field and the evolved knot response against this limit.

## 10. Hidden transverse lattice phase

A discrete bundle is specified not only by its direction but also by its transverse phase relative to the knot.  v0.3 commits hidden coefficients \((u_a,v_a)\) in the local transverse basis and applies

\[
\mathbf d_a=R_{g,\rm ref}(u_a\mathbf e_1+v_a\mathbf e_2).
\]

The same normalized phase set is reused for every topology.  This removes the v0.2 special case in which the centered hexagonal lattice always contained a thread through the bundle center.

## 11. Epistemic classification

A structural PASS verifies the committed numerical/model construction.  A bridge PASS says the committed explicit filament model produced a resolved response.  Neither result by itself derives an SST gravitational law, determines Earth/Sun thread density, or calibrates dimensionless KnotPlot centerlines to SI units.
