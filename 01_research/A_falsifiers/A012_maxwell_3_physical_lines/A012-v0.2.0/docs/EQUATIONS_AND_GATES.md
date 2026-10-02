# Equations and preregistered gates — prefix 3 / v0.2.0

## Historical target being tested structurally

Maxwell's *On Physical Lines of Force* develops an axisymmetric stress state associated with molecular-vortex axes and obtains a dynamic-pressure scaling of the form

\[
\Delta p\propto \rho v^2.
\]

The blind run tests the tensor structure and robustness without reading Maxwell's numerical special-case coefficient.

## Centreline surrogate

Regularized midpoint-segment Biot--Savart kernel:

\[
\mathbf u(\mathbf x)=\frac{\Gamma}{4\pi}
\sum_k\frac{\Delta\boldsymbol\ell_k\times\mathbf r_k}
{(\mathbf r_k^2+a^2)^{3/2}}.
\]

The knot tube thickness from `*.metrics.json` defines the geometry scale. For SI diagnostics the tube thickness is mapped to the SST core radius \(r_c\). The circulation amplitude is calibrated before stress evaluation so that the cross-sectional RMS transverse fluctuation scale equals the preregistered characteristic swirl speed.

## Coarse momentum flux

\[
R_{ij}=\rho_{\!f}\langle u_i'u_j'\rangle,
\qquad
\mathbf u'=\mathbf u-\langle\mathbf u\rangle_{\rm section}.
\]

For section tangent \(\mathbf t\),

\[
p_\parallel=\mathbf t^T R\mathbf t,
\qquad
p_\perp=\tfrac12(\operatorname{tr}R-p_\parallel),
\]

\[
\Delta p=p_\perp-p_\parallel,
\qquad
C_{\rm blind}=\frac{\Delta p}{\rho_{\!f}v_{\rm ref}^2}.
\]

The axisymmetric model tensor is

\[
R_{\rm ax}=p_\perp I+(p_\parallel-p_\perp)\mathbf t\mathbf t^T.
\]

The normalized residual is

\[
\epsilon_{\rm ax}=\frac{\|R-R_{\rm ax}\|_F}{\|R\|_F}.
\]

## Basic/extended gates

Blind thresholds are frozen in `config/basic.json` and `config/extended.json`. They concern source quality, tensor axisymmetry, principal-axis alignment, positive anisotropy, core-regularization robustness, resolution convergence, and parity-evenness.

The unblind comparison is deliberately separate and cannot influence these pass/fail decisions.
