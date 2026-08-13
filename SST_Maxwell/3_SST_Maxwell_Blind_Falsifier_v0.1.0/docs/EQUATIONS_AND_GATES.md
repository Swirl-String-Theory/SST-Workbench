# Equations and preregistered gates

## A. Coarse-grained swirl-stress closure — mandatory

The package does **not** replace the primitive Euler Cauchy stress by an anisotropic material stress. For an inviscid incompressible Euler fluid the primitive stress remains `-p I`. The tested object is the **coarse-grained kinetic / momentum-flux stress**

\[
R_{ij}=\rho_{\!f}\left(\overline{u_i u_j}-\bar u_i\bar u_j\right).
\]

With the coarse vorticity director

\[
n_i=\frac{\bar\omega_i}{\|\bar{\boldsymbol\omega}\|},
\]

the axisymmetric projection is

\[
p_\parallel=n_iR_{ij}n_j,\qquad
p_\perp=\frac{\operatorname{tr}R-p_\parallel}{2},
\]

\[
R^{\rm ax}_{ij}=p_\perp\delta_{ij}+(p_\parallel-p_\perp)n_i n_j,
\qquad
\Delta p_\omega=p_\perp-p_\parallel.
\]

The blind scaling fit is

\[
\ln\Delta p_\omega=b_0+b_\rho\ln\rho_{\!f}+b_v\ln v_{\rm ref}+b_L\ln L.
\]

The preregistered mechanical similarity target tests **exponents only**:

\[
b_\rho\simeq1,\qquad b_v\simeq2,\qquad b_L\simeq0.
\]

No numerical Maxwell coefficient is exposed to this fit.

## B. Reduced-momentum closure — mandatory

Three independently produced vector channels are required:

- material/coherent velocity `u`;
- reduced dynamical momentum `p_red`, obtained independently from the solver/action/impulse response;
- transverse/effective potential `A`, obtained independently from its field sector.

The blind runner fits scalar through-origin maps only on the training subset,

\[
\mathbf p_{\rm red}=\beta_u\mathbf u+\mathbf r_u,
\qquad
\mathbf A=\beta_p\mathbf p_{\rm red}+\mathbf r_p,
\qquad
\mathbf A=\beta_A\mathbf u+\mathbf r_A,
\]

and tests the held-out residuals and the factorization

\[
\beta_A\simeq\beta_p\beta_u.
\]

The value expected from any SST electron normalization is **not read** until unblinding.

## C. Structural/displacement-current closure — optional

Given an independently defined structural displacement field `D_struct` and the residual of the non-storage Ampere channel,

\[
\mathbf Y:=\left(\nabla\times\mathbf H\right)-\mathbf J_{\rm transport},
\]

the runner fits

\[
\mathbf Y=\lambda_D\,\partial_t\mathbf D_{\rm struct}+\mathbf r_D
\]

on alternating training times and judges only held-out times.

## D. Handedness / angular-momentum guard

For matched clockwise/counter-clockwise realizations of otherwise identical geometry,

\[
\mathbf L_+\simeq-\mathbf L_-,\qquad
\Delta p_{\omega,+}\simeq\Delta p_{\omega,-}.
\]

The first condition checks the expected odd angular-momentum response; the second checks that the quadratic stress channel is even. This is also a guard against silently predicting a macroscopic gyroscopic moment from an allegedly isotropic ensemble.

## Decision language

`PASS` means only that the declared closure survives these tests. `FAIL` falsifies that closure within the declared data model. `INCONCLUSIVE` means the scan does not contain enough independent information.
