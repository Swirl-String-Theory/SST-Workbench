# Model notes: what v0.1.0 does and does not test

The dynamical kernel is the regularized midpoint filament law

\[
\mathbf v(\mathbf x)=\frac{\Gamma}{4\pi}\sum_s
\frac{\Delta\boldsymbol\ell_s\times(\mathbf x-\mathbf m_s)}
{\left(|\mathbf x-\mathbf m_s|^2+r_c^2\right)^{3/2}}.
\]

The matching discrete regularized filament Hamiltonian proxy is

\[
H_a=\frac{\rho_{\!f}\Gamma^2}{8\pi}
\sum_{i,j}
\frac{\Delta\boldsymbol\ell_i\cdot\Delta\boldsymbol\ell_j}
{\sqrt{|\mathbf m_i-\mathbf m_j|^2+r_c^2}}.
\]

The Kelvin impulse diagnostic is

\[
\mathbf I=\frac{\rho_{\!f}\Gamma}{2}
\sum_i \mathbf x_i\times\mathbf x_{i+1}.
\]

The Kelvin-duration-like observable is applied to the nonnegative modal intensity
\(S(t)=a(t)^2\):

\[
T_K=\frac{\left(\int S(t)\,dt\right)^2}{\int S(t)^2\,dt}.
\]

For a pure amplitude envelope \(a(t)=a_0e^{-\gamma t}\), this tends to \(T_K=1/\gamma\).
For a persistent undamped signal it grows with the observation window, which is intentionally classified as
`PERSISTENT_OR_UNRESOLVED` rather than forced into a damping interpretation.

## Physicalization assumption

Relaxed centerlines arrive in arbitrary coordinate units. v0.1.0 rescales each uniformly resampled curve so that
half of its minimum nonadjacent point distance (excluding a short arclength neighborhood) equals the canonical
\(r_c\). This is a **tube-radius proxy**, not a canonically established identity for every dataset.
The scale factor is written into every result row.

## Important limitation

`G2_energy_no_loss` is a no-loss test of the regularized filament Hamiltonian under the implemented filament
integrator. It is **not** a full 3-D incompressible-Euler pressure-Poisson proof and does not compute a pressure-flux
surface integral. A later version can add a volumetric pressure-Poisson closure gate without changing the blind
protocol used here.
