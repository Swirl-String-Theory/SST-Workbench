# Circulatiefase als emergente klokdrager

Circulatie heeft dimensie \(L^2/T\) en is daarom niet letterlijk tijd. Door een oppervlakteschaal te kiezen ontstaat een angular rate:

\[
\Omega_\Gamma
=
\frac{\Gamma_{\rm hole}}
{2\pi R_{\rm bundle}^2}.
\]

De geaccumuleerde fase is

\[
\theta_\Gamma(t)
=
\int_0^t\Omega_\Gamma(t')\,dt'.
\]

Voor de bevroren bundels van v0.3.0 is \(\Omega_\Gamma\) constant:

\[
\theta_\Gamma(t)=\Omega_\Gamma t.
\]

De turnoverperiode is

\[
T_\Gamma
=
\frac{2\pi}{|\Omega_\Gamma|}
=
\frac{4\pi^2R_{\rm bundle}^2}
{|\Gamma_{\rm hole}|}.
\]

De outputvelden zijn:

- `clock_omega`;
- `clock_period`;
- `clock_phase`;
- `clock_cycles`;
- tijdens evolutie: `clock_phases` en `clock_cycles`.

Epistemische status:

\[
\boxed{
[\mathrm{RESEARCH\ TRACK}]
\quad
\text{fase-/cyclusteller, niet canonieke proper time.}
}
\]
