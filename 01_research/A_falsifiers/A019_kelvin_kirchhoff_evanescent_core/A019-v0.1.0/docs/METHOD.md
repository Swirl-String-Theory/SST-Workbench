# Numerical method and falsification contract

## 1. Fixed filament model

For each closed component, the centerline is uniformly resampled in arclength. The velocity induced at a target point `x` is evaluated with a segment-midpoint Rosenhead-type regularization,

\[
\mathbf u(\mathbf x)
=\frac{\Gamma}{4\pi}
\sum_j
\frac{\Delta\mathbf s_j\times(\mathbf x-\mathbf x_j^{\rm mid})}
{\left(\lVert\mathbf x-\mathbf x_j^{\rm mid}\rVert^2+a^2\right)^{3/2}}.
\]

The campaign uses the supplied Ridgerunner thickness as the numerical smoothing radius `a` and `Gamma=1` in dataset units. This is a declared regularized filament model, not a finite-core SST derivation.

## 2. Relative equilibrium extraction

For the self-induced centerline velocity, solve

\[
\min_{\mathbf U,\boldsymbol\Omega}
\sum_i
\left\|
\mathbf u_i-\mathbf U-\boldsymbol\Omega\times(\mathbf x_i-\bar{\mathbf x})
\right\|^2.
\]

The dimensionless residual is

\[
\epsilon_{\rm RE}=
\frac{\operatorname{RMS}(\mathbf u-\mathbf u_{\rm rigid})}
{\operatorname{RMS}(\mathbf u)}.
\]

## 3. Rigid-projected shape basis

A periodic parallel-transport frame supplies normal/binormal directions. Constant and Fourier deformations are formed independently on every component and projected against the six global rigid directions. An SVD produces a rank-revealing orthonormal basis `Q`.

## 4. Linearized spectrum

Define `F(X)` as the self-induced velocity after subtracting the best rigid fit. The projected Jacobian is evaluated by fixed forward differences,

\[
A_{ij}
=\left\langle Q_i,
\frac{F(X+hQ_j)-F(X)}{h}
\right\rangle.
\]

The step `h` is frozen in each campaign config as a fraction of the resolved tube thickness.

If \(\lambda_n\) is an eigenvalue of `A`,

\[
\gamma_n=\Re\lambda_n,
\qquad
\sigma_n=|\Im\lambda_n|.
\]

For the corresponding eigenvector field \(\boldsymbol\xi_n(s)\),

\[
k_n^2=
\frac{\int |\partial_s\boldsymbol\xi_n|^2\,ds}
{\int |\boldsymbol\xi_n|^2\,ds}.
\]

Stable-enough modes are selected only by the preregistered growth/frequency filters, not by closeness to a target gap.

## 5. Blind dispersion extraction

The low-`k` training subset fits

\[
\sigma^2=\sigma_0^2+c_{\rm eff}^2k^2.
\]

A separate zero-intercept fit supplies the AIC comparison. The high-`k` subset is held out for prediction. Only after these quantities are frozen is

\[
R_{\rm gap}=\frac{\sigma_0}{2|\Omega_{\rm eff}|}
\]

scored against unity.

## 6. Radial response

A real phase of the lowest sufficiently stable mode perturbs the centerline by a fixed small amplitude. At fixed off-filament probes, the finite-difference field response is measured versus distance. The log-amplitude is fitted both to an exponential and a power law.

The extracted exponential length is compared only afterward with

\[
L_K=\frac{c_{\rm eff}}{2|\Omega_{\rm eff}|}.
\]

## 7. Kirchhoff guard

No centerline-only quantity is relabeled as emissive or absorptive power. Kirchhoff detailed balance remains `NOT_TESTABLE` until a solver provides mode-resolved incident/absorbed/emitted flux under a declared equilibrium or stationary ensemble.
