# Infinite background vortex — model definition and gates

## Physical interpretation

The requested background is interpreted as the \(R_{\rm bg}\to\infty\) limit
of a Rankine vortex. The complete computational domain is on the solid-body
branch:

\[
\mathbf u_{\rm bg}=\Omega_{\rm bg}\,\hat{\mathbf z}\times\mathbf r,
\qquad \zeta_{\rm bg}=2\Omega_{\rm bg}.
\]

This is rotational flow, not potential flow. Its total kinetic energy diverges
in an infinite domain, so the harness treats it only as an externally imposed
local velocity field and does not add a background-energy term.

## SST normalization

Given

\[
\Gamma_{\rm scale}=\alpha c r_c=2v_{\circlearrowleft}r_c=\Gamma_0/\pi,
\]

the corresponding uniform vorticity is

\[
\zeta_{\rm bg}=\Gamma_{\rm scale}/r_c^2=\alpha c/r_c.
\]

Using \(r_c\) as length unit and \(\Gamma_0\) as circulation unit yields

\[
\zeta_{\rm bg}^*=1/\pi.
\]

With the supplied canonical values this corresponds approximately to

\[
\zeta_{\rm bg}=1.55268813\times10^{21}\ {\rm s^{-1}},
\qquad
\Omega_{\rm bg}=7.76344066\times10^{20}\ {\rm s^{-1}}.
\]

These dimensional numbers are provenance labels only; the numerical campaign
uses the dimensionless value \(1/\pi\).

## Preregistered gates

- **BG0 implementation:** background velocity equals \(\Omega\times r\).
- **BG1 residual invariance:** adding the background changes the projected
  relative-equilibrium residual by less than \(10^{-10}\) in a static test.
- **BG2 mirror parity:** trefoil and mirror retain equal parity-even diagnostics.
- **BG3 evolution covariance:** recurrence and shape diagnostics in the
  co-rotating frame agree with the zero-background control within numerical
  error.
- **BG4 no false stabilization:** the background may not be claimed to stabilize
  a trefoil merely because the fitted angular velocity changes.

## Expected theorem

For an isotropic, rotation-equivariant self-induced filament law,

\[
\dot X=F[X]+\Omega\times X

\]

is mapped by \(Y=R(-t)X\) to the no-background equation

\[
\dot Y=F[Y].
\]

Therefore a uniform solid-body background cannot alter shape stability. A
nontrivial stabilizing background must contain strain, differential rotation,
a finite-radius Rankine transition, boundaries, or another non-rigid coupling.
