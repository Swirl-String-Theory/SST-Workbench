# Method — v0.2.0

## 1. Filament dynamics

The carrier and substrate threads share one regularized filament velocity field. For a carrier scale `R=1`, circulation is nondimensionalized by `Gamma_core`; time is compared in

\[
\tau = |\Gamma_K| t.
\]

The local induction coefficient follows the VortexLab convention

\[
\mathbf u_{\rm LIA} = \frac{\Gamma}{4\pi}
\left[\ln\!\left(\frac{2\sqrt{\ell_-\ell_+}}{e^\Delta a}\right)+c_0\right]
\mathbf s'\times\mathbf s'',
\]

with the nonlocal regularized Biot-Savart contribution evaluated by the C++/OpenMP backend.

## 2. Closed threaded substrate

A substrate line has no endpoints. It passes through the central hole and closes through a remote return. In v0.2 different bundle members send their far-return legs into distinct radial sectors; this prevents a common closure direction from manufacturing thread-thread near contacts.

The fixed-total coupling is

\[
\beta = \frac{N_B\Gamma_B}{\Gamma_K}.
\]

The density campaign may instead hold `Gamma_B/Gamma_K` per thread fixed.

## 3. Exact clearance gate

Before anonymous candidate files are created, finite segment-segment distance is evaluated over the complete carrier + thread geometry. The standard preregistration requires

\[
\frac{d_{\min}(t=0)}{a}>2.5.
\]

This is distinct from the later contact-stop threshold (`2.05 a` by default); the gap between 2.5 and 2.05 provides an initial safety margin.

## 4. Shape and local stability

Global translation, rigid rotation and tangential marker gauge are quotiented before the relative-equilibrium residual is evaluated. Perturbations use a parallel-transport-like transverse Fourier basis. The local reduced Jacobian is finite-differenced from `+epsilon/-epsilon` perturbations and its maximum real eigenvalue is recorded.

If contact occurs before the target horizon, ordinary shape-AUC/RPO/Floquet-like local metrics are not used for pair ranking. This avoids rewarding a candidate merely because its trajectory was shorter.

## 5. Pressure-Poisson reconstruction

On a periodic Cartesian grid,

\[
\nabla^2p = -\rho_f\,\partial_i v_j\partial_jv_i.
\]

The zero Fourier mode is removed and the remaining modes are inverted spectrally. The central-minus-shell pressure and spherical radial profile are diagnostics independent of the stability score.

## 6. Free power-law profile

For each anonymous pair, radial bin differences `p_A(r_j)-p_B(r_j)` are formed **before sealing**. The blind analysis searches

\[
p(r)=A+B r^{-\nu}
\]

over a preregistered `nu` grid. For each candidate `nu`, `A,B` are least-squares fitted and the residual is minimized. The search itself does not receive `nu=1` or `nu=2` as a target.

Swapping A and B reverses only the fitted amplitude, not `nu`; therefore the sealed exponent is already the induced active-minus-null exponent up to sign. After sealing, reveal maps identities and compares carrier-median `nu` values with the preregistered Newton target and alternative.

## 7. Pressure coupling law

After reveal, symmetric `+beta/-beta` data decompose

\[
\Delta p(\beta)=A\beta+B\beta^2+C\beta^3+D\beta^4.
\]

The even estimate

\[
B_{\rm even}(|\beta|)\approx
\frac{\Delta p(+\beta)+\Delta p(-\beta)}{2\beta^2}
\]

isolates the leading orientation-independent thread-self contribution; the odd estimate isolates the leading carrier-thread cross term.

## 8. Independent experimental unit

A carrier scanned at many beta values is one geometry, not many independent knots. Therefore inferential signs are computed from carrier-level medians/majorities before the exact sign test. Condition-level counts are retained only as descriptive evidence.

## 9. Stability islands

The long scan maps

\[
(\beta,N_B,N_{\rm helix})\mapsto S_K
\]

for each carrier. Selecting the minimum from this map is multiple-search discovery. v0.2 reports it but never upgrades it to confirmation. A later campaign must fix the selected setting before new blind dynamics are run.

## 10. Triple-gear phase proxy

After global carrier rigid alignment, cyclic parameter shifts of the three carrier components and central threads define geometric phases. Rates are fit from unwrapped phase histories. v0.2 searches small integers `p,q <= 8` for the best relation

\[
p\,\omega_{\rm carrier}\approx q\,\omega_{\rm thread}.
\]

The ratio is discovered rather than supplied. Because remeshing removes material markers, this is explicitly a geometric winding/phase-lock proxy rather than literal tooth transmission.
