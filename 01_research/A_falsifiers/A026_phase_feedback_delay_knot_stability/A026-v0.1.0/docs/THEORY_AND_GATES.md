# Theory and gates

## 1. Baseline dynamics

The numerical baseline is an incompressible inviscid regularized filament model,

\[
\dot{\mathbf X}(s_i)=\frac{\Gamma}{4\pi}\sum_j
\frac{\Delta\mathbf X_j\times(\mathbf X_i-\mathbf X_{j+1/2})}
{(\lVert\mathbf X_i-\mathbf X_{j+1/2}\rVert^2+a^2)^{3/2}},
\]

with adjacent singular segments omitted. This is a falsification surrogate, not a proof of a finite-core SST closure.

## 2. Modal linearization

For each azimuthal/loop index `m`, four normal/binormal sine/cosine perturbations form a projected basis. Central finite differences of the Biot--Savart velocity give a 4x4 shape operator. The preregistered oscillatory branch is the eigenvalue with largest `|Im lambda|`.

## 3. Delay derived, not fitted

From the branch dispersion,

\[
 v_g=\frac{d\omega}{dk},\quad \tau=L/|v_g|,\quad \Theta=\omega\tau.
\]

No target stability metric enters these quantities.

## 4. Nonlinear reveal

The selected eigenmode is applied at fixed amplitude relative to the candidate's non-adjacent gap. Perturbed and unperturbed filaments are evolved independently with identical RK4 settings. Rigid translation/rotation is removed by Kabsch alignment. A log-slope of normalized RMS shape departure is the observed growth metric.

## 5. Blindness

Source filenames are removed before prediction/measurement. `private_reveal/reveal_key.json` is not read by prediction, nonlinear measurement, or evaluation. The evaluation JSON and SHA-256 seals are created before reveal.

## 6. Canonical SST constants

The primary test is dimensionless so that the phase `omega*tau` is not manufactured by an arbitrary physical scale. If a later physical mapping is used, the canonical scales are

\[
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=1.09384563\times10^6\ \mathrm{m\,s^{-1}},\qquad
r_c=1.40897017\times10^{-15}\ \mathrm{m},
\]

and

\[
\Gamma_{\rm SST}=2\pi r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}.
\]

A physical-unit extension must preserve the dimensionless phase prediction.
