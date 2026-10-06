# Pipeline semantics

## Scientific chain

The intended end-to-end chain is

\[
\text{closed-loop geometry}
\rightarrow
\text{linear Euler mode}
\rightarrow
C_k(r,t)
\rightarrow
\{\epsilon,\phi_0\}_{\rm independent}
\rightarrow
\delta\hat k_{\rm phys}
\rightarrow
\delta\ell_{\rm SST}(t)
\rightarrow
\delta s_{\rm SST}(t)
\rightarrow
\delta\phi_{\rm SST}(t)
\rightarrow
I(E,\theta,\tau).
\]

v0.7.0 distinguishes four different objects that must not be conflated:

1. **Finite residual** `K_l(Delta)`: numerical symmetric-control difference at a finite detuning.
2. **Local curvature** `C_k`: second derivative with respect to dimensionless loop wavenumber; phase-covariant and amplitude-free.
3. **Physical action perturbation**: requires an independent physical `delta_k_hat`, complex raw amplitude, and SI scale.
4. **Attosecond phase perturbation**: additionally requires A042/QGI specific action and a physical A029→Volkov time-coordinate map.

## Why `C_k` instead of `K/Delta^2`

The A029 closure condition is

\[
\hat k\hat L+m\Theta_B=2\pi(n+\Delta).
\]

Hence

\[
\delta\hat k=\frac{2\pi\Delta}{\hat L}.
\]

Normalizing by `Delta^2` leaves an explicit loop-length factor in comparisons between geometries.  The v0.7 primary object is therefore

\[
C_k=-\frac{2K}{(\delta\hat k)^2}.
\]

The code still records the finite residual and detuning values so the exact conversion remains auditable.

## Richardson extrapolation

For a smooth symmetric branch,

\[
C_k(\delta\hat k)=C_k(0)+A(\delta\hat k)^2+O(\delta\hat k^4).
\]

Using the two smallest tested offsets `d1>d2`, v0.7 computes

\[
C_k(0)\approx
\frac{d_1^2C_k(d_2)-d_2^2C_k(d_1)}{d_1^2-d_2^2}.
\]

This extrapolated complex time series is the object used for radial-resolution certification and later stages.

## Phase origin

The eigensolver determines a complex eigenvector only up to a global phase.  Therefore `Re(C_k)` with a hard-coded zero phase is not a physical observable.  Stage 03 requires a predictor-clean complex raw modal coefficient projected on the exact same normalized basis:

\[
a(t_0)=\epsilon e^{i\phi_0}.
\]

Only then can Stage 04 construct a real perturbation.

## Physical action

If an independent model/measurement supplies a physical loop-wavenumber displacement, then inside the certified local regime

\[
K_{\rm phys}(t)\simeq -\frac12 C_k(0,t)(\delta\hat k_{\rm phys})^2.
\]

With independent amplitude and phase origin,

\[
\delta\hat\ell(t)=
\epsilon\,\Re\!\left[e^{i\phi_0}K_{\rm phys}(t)\right].
\]

For independent physical core radius `a` and velocity scale `V0`,

\[
\delta\ell(t)=V_0^2\delta\hat\ell(t),
\qquad
\delta s(t)=aV_0\int \delta\hat\ell\,d\hat t.
\]

No canonical SST scale is silently injected into the blind branch.

## Action to quantum phase

When A042 supplies a target-blind specific action scale,

\[
\delta\phi=\frac{\delta s}{(\hbar/m)_{\rm QGI}}.
\]

The numerator is not tuned to that denominator.  If A042 provides an uncertainty, v0.7 propagates the denominator uncertainty into the phase array.

## Attosecond mapping

Stage 07 accepts a matrix

\[
M_{jt}
\]

that maps the certified A029 action-time vector onto the Volkov integration-time grid.  The mapping manifest must be frozen, have zero fitted phase parameters, and contain the exact Stage-04 action-file SHA-256.  A bundle directly supplying a hand-chosen `delta_specific_action` is not accepted by this v0.7 contract.
