# C9 — Iso-Gamma/A dynamic-clock falsification campaign

## Research question

Test the claim

\[
\boxed{\text{not circulation alone, but circulation per area determines the clock rate}}
\]

in a form that can fail.

The surface is preregistered as the cross-sectional area of the imposed axial bundle:

\[
A_{\rm bundle}=\pi R_{\rm bundle}^{2},
\qquad
\bar\zeta=\Gamma_{\rm hole}/A_{\rm bundle}.
\]

For each iso-family, the code changes \(R_{\rm bundle}\) and sets

\[
\Gamma_{\rm hole}=\bar\zeta A_{\rm bundle},
\]

so \(\Gamma/A\) is held fixed while \(\Gamma\) and \(A\) separately change.

## Independent dynamic measurement

The predicted rate is not used to measure the output. The evolving trefoil provides a complex geometric multipole

\[
M_m(t)=\left\langle\left(\frac{x+iy}{r_{\rm rms}}\right)^m\right\rangle,
\qquad m=3\ \text{for the trefoil}.
\]

Its observed orientation phase is

\[
\phi_{\rm obs}(t)=\frac{1}{m}\operatorname{unwrap}\arg M_m(t).
\]

A linear regression gives an observed rate \(\Omega^{\rm obs}\). A matched isolated trefoil is evolved with the same numerical protocol, and its self-induced rate is subtracted:

\[
\Delta\Omega_{\rm dyn}
=
\Omega_{\rm bundle}^{\rm obs}-\Omega_{0}^{\rm obs}.
\]

The independently extracted dynamic period is

\[
T_{\rm dyn}=\frac{2\pi}{|\Delta\Omega_{\rm dyn}|}.
\]

Only after this extraction is the prescribed mean vorticity used to form

\[
\boxed{
\mathcal Q_\Gamma
=
\frac{2\Delta\Omega_{\rm dyn}}{\Gamma/A}
}.
\]

The hypothesis predicts \(\mathcal Q_\Gamma=1\).

## Two period gates

### Primary instantaneous phase-rate gate

The initial phase is fitted over a fixed preregistered time window. Because a directly observed unwrapped phase is regressed, this gate can measure a rate from a partial cycle. Required controls include:

- minimum multipole amplitude;
- minimum sample count;
- high phase-linearity \(R^2\);
- high signal-to-uncertainty for the background-induced rate.

This produces the primary \(T_{\rm dyn}\) and \(\mathcal Q_\Gamma\).

### Secondary strict multi-cycle gate

The full observation window is also fitted. Certification requires at least three measured orientation cycles. This is deliberately stricter and may remain inconclusive when the trefoil rotates much more slowly than \(\bar\zeta/2\).

Intrinsic shape observables are separately searched for a period using FFT and autocorrelation consensus. They are not substituted for the primary geometric phase when no shape period is certified.

## Preregistered falsifiers

Per run:

\[
|\mathcal Q_\Gamma-1|<0.02.
\]

Across equal-\(\Gamma/A\) continuum runs:

\[
\max \mathcal Q_\Gamma-
\min \mathcal Q_\Gamma<0.02.
\]

A certified violation falsifies the claim within the frozen straight-bundle model. An uncertified period produces `INCONCLUSIVE`, not a pass.

## Positive control

`C9_solid_body_positive_control.json` deliberately uses a bundle radius large enough that the whole trefoil lies inside the uniform-vorticity branch. In that case the background is solid-body rotation and the extractor must recover

\[
\mathcal Q_\Gamma\simeq1.
\]

This control is mathematical, not the physical hole-contained bundle hypothesis.

## Physical iso-Gamma/A test

`C9_iso_gamma_area_smoke.json` keeps the bundle inside the central aperture. The trefoil therefore lies mainly outside the vorticity-carrying cross-section and samples the exterior \(1/r\) velocity field. This is the direct falsifier of the claim that the bundle-average \(\Gamma/A\) alone fixes the trefoil's observed clock rate.

## Epistemic boundary

A negative result applies to:

- frozen straight axial tubes or their continuum Rankine limit;
- the selected bundle area;
- the trefoil multipole phase observable;
- the scanned numerical regime.

It does not settle full 3-D tube backreaction, dynamically selected area, or the identification of this phase clock with proper time.
