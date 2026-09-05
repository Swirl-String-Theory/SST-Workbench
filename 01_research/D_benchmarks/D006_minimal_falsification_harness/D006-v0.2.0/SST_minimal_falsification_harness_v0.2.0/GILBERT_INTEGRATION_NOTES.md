# Gilbert Database Integration Notes

## Source

The package now reads the uploaded Brian Gilbert database directly
(\cite{Gilbert2016} / XML header Author/Title/Date):

- database title: `Database of Ideal Knots 3-10 crossings`
- author: Brian Gilbert
- date: 6/11/2016 2:12:11 p.m.
- source record for the trefoil: `3:1:1`
- reported trefoil values:
  \[
  L=16.371637,\qquad D=1,\qquad \mathcal L_D=16.371637.
  \]
- retained nonzero Fourier records for `3:1:1`: 183
- highest listed Fourier mode: 250

The parser uses

\[
\mathbf X(t)=\sum_n
\left[
\mathbf A_n\cos(nt)+\mathbf B_n\sin(nt)
\right].
\]

## Usability gate (`C_cont`)

Roughly 144 of ~250 AB records reconstruct without self-contact and with
\(\hat\kappa_{\max}=2\) exactly (curvature-only artifacts). Before treating a
record as ideal, require the thickness-partition score

\[
C_{\mathrm{cont}}>0.05
\]

(implemented in SST-Workbench `sst_gilbert_usability.py`). Batch loaders skip
rejected IDs and report counts. Escape hatch for diagnostics only:
`--allow-curvature-only`.

On the usable contact set (~106 knots, 3–10 crossings):
\(I_{\kappa^2}/L_D=1.0587\pm0.0699\) (6.6%). Circle `0:1:1` gives
\(I_{\kappa^2}/L_D=4\) exactly; trefoil writhe magnitude ≈ 3.417.

## Why two lengths are reported

The database coefficients are printed to finite decimal precision. For `3:1:1`
the current reconstruction gives approximately

\[
\mathcal L_D^{\rm Fourier}\approx16.37246043,
\]

whereas the database metadata reports

\[
\mathcal L_D^{\rm metadata}=16.371637.
\]

Therefore:

- the leading term \((8\pi/3)\mathcal L_D\) uses the database metadata by default;
- curvature and contact features use the Fourier reconstruction;
- the difference is explicitly recorded and never silently absorbed into
  \(\Delta\).

## Current trefoil diagnostics

With the packaged defaults and automatic sampling floor:

\[
\mathcal I_{\kappa^2}
=
\int(D\kappa)^2\frac{ds}{D}
\approx19.44782476,
\]

\[
\mathcal C_{\rm contact}\approx0.18698472.
\]

These are not universal constants. They depend on:

- Fourier coefficient precision;
- centerline sample count;
- contact-shell width;
- orthogonality tolerance;
- core-overlap model.

They must undergo convergence and profile-sensitivity tests before entering a
physical falsification claim.

## Cross-knot inventory

The packaged batch contains 21 single-component records:

\[
0_1,\ 3_1,\ 4_1,\ 5_1,\ 5_2,\ 6_1,\ 6_2,\ 6_3,\ldots,11_2.
\]

Multi-component links are skipped because the current response functional does
not yet contain inter-component kernels.

## Scientific verdict

The database materially improves the geometry stage and eliminates the previous
30-mode fallback for the trefoil. It does not supply the independent dynamical
observables needed to determine the Wilson coefficients. Therefore it enables
stronger geometry and universality tests but does not by itself predict

\[
\Delta_{3_1}\simeq-0.117284.
\]
