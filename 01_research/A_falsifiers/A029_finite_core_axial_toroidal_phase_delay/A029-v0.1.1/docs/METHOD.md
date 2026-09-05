# Method: finite-core eigenmodes, symmetric closure controls and emergent loop delay

## 1. Local finite-core operator

The base flow is

\[
\mathbf V_0(r)=V_\theta(r)\mathbf e_\theta+U_s(r)\mathbf e_s,
\]

and perturbations are

\[
\delta q=\hat q(r)e^{i(m\theta+ks)+\lambda t}.
\]

The code solves the primitive-variable linearized incompressible-Euler generalized eigenproblem with Chebyshev radial collocation. Selected modes must be core-localized, axial/toroidal hybridized, low-residual and convergent over the preregistered radial ladder.

## 2. Closed carrier and Bishop holonomy

The finite core is local/radial; the closed knot or link supplies the global slender-tube length, curvature validity and Bishop parallel-transport holonomy \(\Theta_B\). Exact closure obeys

\[
\boxed{k_0a=\frac{2\pi n-m\Theta_B}{L/a}}.
\]

## 3. v0.1.1 symmetric control

The v0.1.0 control sampled only one non-integer offset, so an ordinary dispersion slope could mimic a closure advantage. v0.1.1 evaluates both

\[
k_-=k_0-\Delta k,\qquad k_+=k_0+\Delta k,
\]

and defines the control growth by their average. To first order in \(\Delta k\),

\[
\frac{g(k_0-\Delta k)+g(k_0+\Delta k)}2
=g(k_0)+\frac12g''(k_0)\Delta k^2+O(\Delta k^4).
\]

The linear \(g'(k_0)\Delta k\) term is removed.

## 4. Delay is measured, never supplied

The tracked branch gives \(\omega(k)\), hence

\[
v_g=\frac{d\omega}{dk},\qquad \tau_g=\frac{L}{|v_g|}.
\]

A narrow packet is propagated using the measured local dispersion polynomial and the first coherent periodic return gives \(\tau_{ret}\). The return phase is an output.

## 5. Swirl-Clock observables

For \(\lambda=\sigma+i\omega_\lambda\), the CLOSED case exports

\[
\Re\lambda=\sigma,\quad
\Im\lambda=\omega_\lambda,\quad
T_{mode}=\frac{2\pi}{|\Im\lambda|},
\]

plus \(v_g\), \(\tau_g\), \(\tau_{ret}\), \(\phi_{loop}\), the core RMS material swirl \(\Omega_{swirl}\), and \(|\Im\lambda|/\Omega_{swirl}\).

## 6. Stability and phase tests

Generic closure statistics use only both-valid, non-neutral CLOSED/control comparisons. The generic phase test remains leave-one-carrier-out and does not prescribe a phase optimum.

A separate confirmatory campaign uses the prior discovery-only \(m=1\) target \(\phi_\star=2.72\) rad on new carriers. It tests the predetermined directional prediction that growth relative to the symmetric control decreases as \(\cos(\phi-\phi_\star)\) increases.

## 7. Limits

This remains a slender finite-core local-to-global mechanism test. Curvature and torsion are not yet embedded inside a full curved-tube 3-D Euler operator. A positive result motivates curved finite-core Euler/Floquet and nonlinear orbital-stability calculations; it is not proof of a complete SST particle model.
