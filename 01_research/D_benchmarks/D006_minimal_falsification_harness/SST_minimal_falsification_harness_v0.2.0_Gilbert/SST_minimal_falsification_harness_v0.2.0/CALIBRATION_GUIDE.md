# What belongs in `calibration_template.json`?

The file is **not** filled with knot ropelengths. The Gilbert database supplies
geometric features, but it does not supply the independent dynamical response
needed to determine the coefficients of \(\Delta\).

For every calibration row, the required equation is

\[
y_n=
\mathscr R_{\rm micro}[\gamma_n,f_n,\Omega_{3,n}]
-\frac{8\pi}{3}\mathcal L_{D,n}
=
\sum_a A_{na}c_a.
\]

Here:

- `value` is the computed \(y_n\), obtained from a core-resolved microscopic
  response calculation;
- `sigma` is its numerical or experimental uncertainty;
- `features` contains the row \(A_{na}\), such as
  \(I_{\kappa^2}\), \(I_{\Omega^2}\), and \(C_{\rm contact}\);
- `provenance.source` identifies the simulation output or measurement;
- `provenance.derivation` gives the equation mapping that output to \(y_n\);
- `provenance.used_constants` lists every input, proving that no
  \(\alpha\)-derived quantity entered the calibration.

## Important correction to v0.1/v0.2

A free feature `length` should normally be removed from \(\Delta\), or fixed by
the renormalization condition

\[
c_L=0.
\]

Otherwise

\[
\Delta=c_L\mathcal L_D+\cdots
\]

is degenerate with the leading coefficient \(8\pi/3\), and \(c_L\) can simply
absorb the desired trefoil discrepancy. That would not be an independent
prediction.

The recommended minimal model is therefore

\[
\Delta=
c_\kappa I_{\kappa^2}
+c_\Omega I_{\Omega^2}
+c_C C_{\rm contact}.
\]

## What `ideal_favorites.txt` contributes

For each knot it provides:

\[
\mathcal L_D,\qquad
I_{\kappa^2},\qquad
C_{\rm contact}
\]

after Fourier reconstruction. These are the **right-hand-side features**.
It does not provide the left-hand-side calibration values \(y_n\).

## Required independent campaigns

1. Circular rings with several \(R/D\): determine \(c_\kappa\).
2. Straight periodic twisted tubes: determine \(c_\Omega\).
3. Antiparallel finite-core pairs at several separations: determine \(c_C\).
4. Mixed geometries: holdouts, never used for fitting.
5. Trefoil `3:1:1`: final frozen test only.

Ring energy or Kelvin-wave dispersion may constrain the same microscopic core
model. They may not be entered directly as `value` unless a derivation proves
that they evaluate the same response operator \(\mathscr R_{\rm micro}\).
