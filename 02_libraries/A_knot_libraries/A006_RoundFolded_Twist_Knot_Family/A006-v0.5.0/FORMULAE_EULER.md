# VCCR v0.2.0 independent affine Euler benchmark — derivation

We verify the classical unforced incompressible Euler equations:

$$
\nabla\cdot\mathbf{u}=0,\qquad
\partial_t\mathbf{u}+(\mathbf{u}\cdot\nabla)\mathbf{u}=-\rho^{-1}\nabla p.
$$

Choose constant axial strain rate \(k>0\) and initial angular velocity \(\Omega_0>0\):

$$
\mathbf{u}(\mathbf{x},t)=
\begin{pmatrix}
-kx/2-\Omega(t)y\\
\Omega(t)x-ky/2\\
kz
\end{pmatrix},\qquad \Omega(t)=\Omega_0 e^{kt}.
$$

Writing \(\mathbf{u}=M(t)\mathbf{x}\), we find \(\mathrm{tr}\,M=0\) and

$$
\dot M+M^2=\mathrm{diag}(k^2/4-\Omega^2,\;k^2/4-\Omega^2,\;k^2),
$$

which is symmetric **only if** \(\dot\Omega=k\Omega\). Therefore a pressure that solves Euler exactly is

$$
\frac{p(\mathbf{x},t)}{\rho}=-\frac12\left[
\left(\frac{k^2}{4}-\Omega(t)^2\right)(x^2+y^2)+k^2 z^2\right]+C(t).
$$

Divergence and Euler momentum are checked numerically by finite differences independently of the analytic matrix derivation.

The fluid vorticity is

$$
\boldsymbol{\omega}=\nabla\times\mathbf{u}=2\Omega(t)\hat{\mathbf z},\qquad
\frac{D\boldsymbol\omega}{Dt}=(\boldsymbol\omega\cdot\nabla)\mathbf{u}=k\boldsymbol\omega.
$$

The material flow map has \(z(t)=z_0 e^{kt}\) and \(r(t)=r_0 e^{-kt/2}\), plus an azimuthal rotation by \(\int_0^t \Omega(s)\,ds\). Hence

$$
\lambda=e^{kt},\quad
A(t)/A_0=e^{-kt}=\lambda^{-1},\quad
V(t)=A(t)L(t)=V_0,
$$

$$
\Gamma(t)=2\Omega(t)A(t)=2\Omega_0 A_0=\Gamma_0,\qquad
\frac{a_{\rm eff}(t)}{a_{\rm eff}(0)}=\lambda^{-1/2}.
$$

These are **predictions** against which numerical polygon ring measurements are tested. Particle positions are propagated by independent fourth-order Runge–Kutta integration of Euler velocity, **without evaluating** the VCCR closure to set area or radius. A finite-difference curl provides another vorticity observable; pressure and divergence residuals are independent probes.

The benchmark defines dimensionless \(k=0.4\), \(\Omega_0=1\), \(a_0=1\), \(L_0=12\). No dimensional SST pressure or strain rate is inferred. Rescaling the algebra to \(r_c\) or the characteristic swirl speed is *only* a conditional similarity map, **not experimental calibration**.

**Finite-energy limitation:** the affine flow is unbounded and velocity grows linearly in position. Uniformly distributed vorticity extends outside the chosen material marker tube; therefore its surface is **not** the boundary of a localized, isolated vortex core. The chosen markers are a material control volume, not a self-contained finite-core vortex. This release cannot qualify knotted vortex stability.

**Elliptic counterexample:** Initially take a material ellipse with semiaxes \(a_0 q\) and \(a_0/q\). It has \(A_0=\pi a_0^2\) regardless of \(q\), and thus the same area-equivalent radius. Yet its geometric boundary radii differ. A radius closure must specify which radius is meant.

**Dimensional checks:** for a dimensional Euler field, \([k]=[\Omega]={\rm s^{-1}}\), \([\mathbf u]={\rm m\,s^{-1}}\), \([\omega]={\rm s^{-1}}\), \([p/\rho]={\rm m^2\,s^{-2}}\), \([\Gamma]={\rm m^2\,s^{-1}}\), \([A]={\rm m^2}\), \([V]={\rm m^3}\). In the packaged benchmark these are scaled dimensionlessly; the native interface instead expects SI values.

**Terminology:** The conserved invariant in the non-baroclinic, incompressible Euler material-tube setting is Kelvin circulation / transported vorticity flux. The pointwise magnitude of vorticity is generally **not conserved** during stretching. Ertel *potential vorticity* requires a suitable advected scalar field; it must not be equated with the circulation invariant used here.