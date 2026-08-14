# Theory, gates, and failure semantics

## T01 — Material swirl-tonic potential

Define, as a kinematic alias only,

\[
\mathbf A_{\rm st}^{(m)} := \mathbf v,
\qquad
\boldsymbol\zeta := \nabla\times\mathbf v
=\nabla\times\mathbf A_{\rm st}^{(m)}.
\]

For any smooth orientable surface $S$ with boundary $C=\partial S$,

\[
\Gamma_C
=\oint_C\mathbf v\cdot d\boldsymbol\ell
=\int_S\boldsymbol\zeta\cdot d\mathbf S.
\]

Dimension checks:

\[
[\mathbf v]=\mathrm{m\,s^{-1}},\quad
[\boldsymbol\zeta]=\mathrm{s^{-1}},\quad
[\Gamma]=\mathrm{m^2\,s^{-1}}.
\]

This is not an SST gauge symmetry. $\mathbf v$ is the physical material velocity. Adding a gradient can preserve curl locally while changing trajectories, kinetic energy, and boundary data. A harmonic-knot field can also change global circulation periods without changing curl.

**Demo gate:** independent line and surface quadratures converge to the same Stokes value, and the finite-difference divergence/curl residuals converge.

## T02 — Topological holonomy

For thin disjoint vortex filaments $\gamma_i$,

\[
\Gamma_C
\simeq
\sum_i \Gamma_i\,Lk(C,\gamma_i).
\]

Define

\[
h_C=\frac{\Gamma_C}{\Gamma_0}.
\]

The test compares a Biot--Savart line integral with an independently computed Gauss linking number. Orientation reversal must flip both quantities. Mirror/chirality changes are not, by themselves, equivalent to changing circulation sign.

**Primary metric:**

\[
\epsilon_{\rm hol}
=\frac{|\Gamma_C-\Gamma_{\rm top}|}
{\max(|\Gamma_{\rm top}|,\epsilon)}.
\]

## T03 — Moving-loop identity

For a loop $C(t)$ moving with velocity $\mathbf u_C$ in an incompressible inviscid Euler flow,

\[
\frac{d\Gamma_C}{dt}
=
\oint_{C(t)}
[(\mathbf v-\mathbf u_C)\times\boldsymbol\zeta]
\cdot d\boldsymbol\ell.
\]

The positive control uses the exact steady Euler shear

\[
\mathbf v=(a y^2,0,0),
\qquad
\boldsymbol\zeta=(0,0,-2ay),
\]

and a rectangular loop translated in $y$ at speed $U$. Analytically,

\[
\frac{d\Gamma_C}{dt}=-2aLHU.
\]

A material loop ($\mathbf u_C=\mathbf v$ pointwise) gives the Kelvin limit $d\Gamma/dt=0$.

## T04 — Exterior Hodge/harmonic circulation sector

Outside resolved vortex support,

\[
\nabla\times\mathbf v=0,
\qquad
\nabla\cdot\mathbf v=0,
\]

while non-contractible periods can remain non-zero. A reduced representation is

\[
\mathbf v_{\rm ext}
=\nabla\phi+
\sum_i\Gamma_i\mathbf h_i,
\]

where each $\mathbf h_i$ is normalized to unit circulation around the corresponding meridian. The package uses filament Biot--Savart basis fields as numerical representatives of the harmonic circulation sector and allows a constant harmonic-gradient nuisance field in the reduced fit.

This is a reduced audit, not a full finite-element Hodge solver.

## T05 — Energy/helicity stationarity

For kinetic energy

\[
E[\mathbf v]
=\frac{\rho}{2}\int |\mathbf v|^2\,dV
\]

and helicity

\[
H[\mathbf v]
=\int\mathbf v\cdot\boldsymbol\zeta\,dV,
\]

stationarity at fixed $H$ requires a Lagrange multiplier $\lambda$ such that

\[
\delta E=\lambda\,\delta H.
\]

The field positive control is the ABC Beltrami flow with $A=B=C=1$, for which

\[
\nabla\times\mathbf v=\mathbf v.
\]

For a centerline, the package also evaluates a regularized filament-energy diagnostic and a discrete writhe proxy. Across smooth paired perturbations it fits

\[
dE_j\simeq\lambda\,dH_j
\]

and reports the normalized residual. This centerline test is deliberately diagnostic: a ropelength optimum is not assumed to be an Euler-energy optimum.

## T06 — Cyclic work and chirality response

For a quasistatic linear response $\mathbf F=K\mathbf q$,

\[
K=K_s+K_a,
\qquad
K_s=\frac{K+K^T}{2},
\qquad
K_a=\frac{K-K^T}{2}.
\]

A force derived from a scalar quadratic potential has a symmetric Jacobian. For a closed quasistatic loop,

\[
W_{\rm cyc}=\oint\mathbf F\cdot d\mathbf q=0.
\]

A persistent nonzero cycle integral falsifies that passive conservative closure unless a separate dynamic reservoir, hysteresis, or gyroscopic/non-quasistatic term is explicitly modeled.

## T07 — Derived radial force-flux

For any proposed gravity-like acceleration field $\mathbf g_\star$, define

\[
\Phi_g(r)=\oint_{S_r}\mathbf g_\star\cdot d\mathbf S.
\]

A Newtonian-like exterior monopole requires approximately

\[
\Phi_g(r)=\mathrm{const},
\qquad
\langle g_r\rangle\propto r^{-2},
\qquad
\frac{|\langle g_r\rangle|}{\sqrt{\langle g_r^2\rangle}}\approx1.
\]

The built-in negative control takes the compact-vortex exterior Bernoulli pressure candidate

\[
p-p_\infty=-\frac12\rho |\mathbf v|^2,
\qquad
\mathbf g_p=-\frac1\rho\nabla p
=\frac12\nabla |\mathbf v|^2.
\]

For a compact vortex with far-field $|\mathbf v|=O(r^{-3})$, this has a characteristic magnitude $O(r^{-7})$, not $O(r^{-2})$. It should therefore reject the Newtonian-monopole gate.

## Default thresholds

Thresholds are software/audit defaults, not constants of nature. They are configurable in `examples/demo_config.json`.

- T01 Stokes relative error: $<10^{-4}$ on the highest demo resolution.
- T02 holonomy relative error: $<2\times10^{-2}$ with the supplied midpoint filament kernel; high-resolution/native runs should tighten this.
- T03 moving-loop relative error: $<10^{-4}$.
- T04 exterior normalized curl/divergence: $<5\times10^{-2}$ in the demo.
- T05 Beltrami residual: $<10^{-3}$ in the positive control.
- T06 normalized cyclic work: $<10^{-6}$ for the conservative positive control.
- T07 Newtonian candidate: radial coherence $>0.9$, fitted exponent $|n-2|<0.25$, and shell-flux coefficient of variation $<0.15$. The built-in compact-vortex pressure candidate is expected to fail.
