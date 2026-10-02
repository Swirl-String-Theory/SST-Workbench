# SST-21D output schema v0.2

## Fresnel inventory

`fresnel_inventory.csv` has one row per shared filename stem and reports whether `.fseries` and `.short` representations exist.

Key fields:

- `topology_key`: parent-directory label, e.g. `3_1`.
- `variant_key`: full variant, e.g. `3_1p`.
- `fseries_field_width = 6` and `short_field_width = 3`.
- `fseries_first_numeric_tokens`: exact lexical first row.
- `fseries_zero_token_styles`: observed spellings such as `0.000` or `0.000000`.
- `harmonic_origin`: selected implicit Fourier start index, `0` or `1`.
- `origin_method`: paired-shape fit, explicit comment, user override, or documented fallback.
- `origin_status`: `RESOLVED`, `LOW_CONFIDENCE`, or `AMBIGUOUS`.

## Fourier representation

For row number `r=0,...,M-1` and inferred origin `nu`,

\[
\mathbf X(t)=\sum_{r=0}^{M-1}
\left[\mathbf A_r\cos((r+\nu)t)+\mathbf B_r\sin((r+\nu)t)\right].
\]

The six columns are

\[
(a_x,b_x,a_y,b_y,a_z,b_z).
\]

## `.short` representation

Each numeric row is exactly

\[
(x_i,y_i,z_i).
\]

Comment lines beginning with `%`, `#`, `;`, or `//` are ignored. Decimal precision does not affect parsing.

## Master and representation tables

`sst21d_fresnel_master.csv` contains one row per variant pair. It selects one representation for the common SST-21D geometry columns and also contains representation-agreement fields.

`fresnel_representations.csv` contains one row per actual source file representation.

Cross-representation fields include:

- `fseries_short_shape_rmsd`;
- `fseries_to_short_length_ratio`;
- `fseries_to_short_rms_radius_ratio`;
- `fseries_short_agreement_status`.

Shape RMSD is scale independent. Length and radius ratios retain the source scaling difference.

## Static geometry

For a closed polygon with vertices `x_i`,

\[
L_N=\sum_i\lVert\mathbf{x}_{i+1}-\mathbf{x}_i\rVert.
\]

The discrete circumcircle curvature proxy is

\[
\kappa_i=
\frac{2\lVert(\mathbf{x}_i-\mathbf{x}_{i-1})\times
(\mathbf{x}_{i+1}-\mathbf{x}_i)\rVert}
{\lVert\mathbf{x}_i-\mathbf{x}_{i-1}\rVert
 \lVert\mathbf{x}_{i+1}-\mathbf{x}_i\rVert
 \lVert\mathbf{x}_{i+1}-\mathbf{x}_{i-1}\rVert}.
\]

The sampled reach proxy is

\[
r_{\rm reach}^{\rm proxy}
=
\min\left(\frac{1}{\kappa_{\max}},\frac{d_{\rm nonlocal}}{2},
\frac{d_{\rm inter}}{2}\right).
\]

The package reports

\[
\mathcal R_{\rm radius}^{\rm proxy}=\frac{L}{r_{\rm reach}^{\rm proxy}},
\qquad
\mathcal R_D^{\rm proxy}=\frac{L}{2r_{\rm reach}^{\rm proxy}}.
\]

These are sampled diagnostics, not exact thickness certificates.

## Dynamic fields

Static source rows leave the following unset:

```text
Q_phase
Dmin_projected_det1
phase_structure_ir_exponent
dispersion_exponent_p
damping_proxy
```

They require a trajectory and, where relevant, an explicit material-phase field.
