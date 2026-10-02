# Theory and falsification target

The package tests the direct chain

\[
\mathbf v\to g^{\rm eff}_{\mu\nu}\to d\tau/dt\to \Phi_{\rm SST}=-\tfrac12v^2\to p/\rho_{\!f}\to Q,
\qquad Q=\tfrac12|\boldsymbol\omega|^2-S_{ij}S_{ij}.
\]

For the shift metric

\[
ds^2=-c^2dt^2+|d\mathbf x+\mathbf v\,dt|^2,
\]

\(\det g=-1\) and a stationary clock obeys

\[
\frac{d\tau}{dt}=\sqrt{1-v^2/c^2}.
\]

In the weak-field comparison \(g_{00}\simeq-(1+2\Phi/c^2)\), this gives

\[
\Phi_{\rm SST}=-\frac12v^2.
\]

A Newtonian monopole \(\Phi=-GM/r\) therefore requires

\[
v^2\propto r^{-1},\qquad v\propto r^{-1/2}.
\]

For incompressible Euler flow,

\[
\nabla^2(p/\rho_{\!f})=-\partial_i v_j\partial_j v_i
=\frac12|\boldsymbol\omega|^2-S_{ij}S_{ij}\equiv Q.
\]

The package evaluates the pressure-Poisson integral through its exact divergence-theorem surface form for the reconstructed field,

\[
I_Q(R)=\int_{V_R}Q\,dV
=-\oint_{S_R}[(\mathbf v\cdot\nabla)\mathbf v]\cdot\mathbf n\,dS.
\]

If \(p/\rho_{\!f}\simeq\Phi_{\rm SST}\), it independently evaluates

\[
I_\Phi(R)=\oint_{S_R}\nabla\Phi_{\rm SST}\cdot\mathbf n\,dS
=-\oint_{S_R}(\nabla\mathbf v)^T\mathbf v\cdot\mathbf n\,dS.
\]

For a nonzero monopole both should approach \(4\pi GM\), and the shell amplitude estimator

\[
\mu_{v^2}(R)=\frac12R\langle v^2\rangle_{S_R}
\]

should plateau at \(GM\).

## Reconstruction model

A relaxed centerline alone does not contain a unique 3-D velocity field. The package therefore preregisters a regularized filament reconstruction,

\[
\mathbf v(\mathbf x)=\frac{\Gamma}{4\pi}\oint
\frac{d\boldsymbol\ell\times(\mathbf x-\mathbf X)}{(|\mathbf x-\mathbf X|^2+a^2)^{3/2}}.
\]

Each centerline is uniformly resampled and normalized so its estimated rope thickness is one core radius. Physical conversion then sets that radius to canonical \(r_c\) and uses \(\Gamma=2\pi r_c\mathbf v_{\!\boldsymbol{\circlearrowleft}}\).

A failure therefore falsifies the **direct regularized-filament closure**, not every conceivable SST long-range completion.
