# Scientific protocol: E3 → E4 → E5 → E2 → E1

## E3

For a uniform Galilean boost `U`, the regularized Biot–Savart filament dynamics should obey

\[
\mathbf X_B(\tau)=\mathbf X_0(\tau)+\mathbf U\tau
\]

when both runs start from the same intrinsic curve. The test therefore compares

\[
\delta_X=\frac{\operatorname{RMS}\!\left[\mathbf X_B-\mathbf U\tau-\mathbf X_0\right]}
{\operatorname{RMS}\!\left[\mathbf X_0-\bar{\mathbf X}_0\right]}.
\]

The same objectivity requirement is applied to energy, impulse and an intrinsic curvature Fourier mode.

## E4

For a family of Kelvin-like excitations with amplitude `A`,

\[
\mathcal J(A)=\frac{\Delta E(A)}{\nu(A)}.
\]

Dimensions:

\[
[\mathcal J]=\frac{\mathrm J}{\mathrm{s}^{-1}}=\mathrm{J\,s}.
\]

The hypothesis tested is not that `J` equals a known constant. It is the prior question whether `J` is internally amplitude-independent and boost-objective.

## E5

Hydrodynamic impulse for a closed filament is

\[
\mathbf I=\frac{\rho\Gamma}{2}\oint \mathbf X\times d\mathbf X,
\]

with units kg m s\(^{-1}\). For an axisymmetric translating family an operational inertia proxy is

\[
M_I=\frac{I_z}{U_z},
\]

which has units kg. For a symmetric standing internal excitation,

\[
C_{\rm blind}^2=\frac{\Delta E}{\Delta M_I},
\qquad
[C_{\rm blind}]=\mathrm{m\,s^{-1}}.
\]

The test requires linearity, a small intercept, low amplitude scatter and cross-resolution stability. It does not identify `C_blind` with any pre-existing speed.

## E2

For the intrinsic mode phase `phi(t)`, remove a fitted coherent drift:

\[
\delta\phi(t)=\phi(t)-(\Omega t+\phi_0).
\]

The residual increments are tested for a finite decorrelation lag. Beyond it, the mean-square increment is fitted to

\[
\left\langle[\delta\phi(t+\tau)-\delta\phi(t)]^2\right\rangle\propto\tau^\alpha.
\]

A normal diffusive closure requires `alpha` near one over a resolved interval.

## E1

A fixed positive-transfer event detector produces event sizes `e_i`. A candidate spacing `q` is learned only on a training subset by minimizing distance to the nearest positive integer multiple:

\[
R(q)=\sqrt{\frac1N\sum_i\left(\frac{e_i}{q}-\operatorname{round}\frac{e_i}{q}\right)^2}.
\]

The selected `q` is then evaluated on held-out events and against continuous lognormal surrogate data. Stability across independently generated amplitude series is mandatory.

## Scope limitation

The package advances regularized closed vortex filaments. It does not simulate viscosity, reconnection, compressibility, a separate photon/torsion field, or full three-dimensional Euler vorticity. Consequently E5 is an inertial-closure analogue and E1 uses a modal-energy proxy; neither is to be reported as a direct photon calculation.
