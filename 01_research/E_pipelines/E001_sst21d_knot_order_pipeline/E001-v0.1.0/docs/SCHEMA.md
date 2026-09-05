# SST-21D output schema

## Static identity and provenance

- `catalog_id`: original Gilbert ID, e.g. `3:1:1`.
- `topology_key`: normalized label, e.g. `3_1`; multi-component labels use `2^2_1`.
- `catalog_topology_status`: `CATALOG_LABEL_ONLY_NOT_RECOMPUTED`.
- `source_entry_sha256`: hash of the exact XML element.
- `source_L`, `source_D`: catalogue values.

## Geometry

For a closed polygon with vertices \(\mathbf{x}_i\):

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

The sampled reach/DCSD proxy is

\[
r_{\rm reach}^{\rm proxy}
=
\min\left(\frac{1}{\kappa_{\max}},\frac{d_{\rm nonlocal}}{2},
\frac{d_{\rm inter}}{2}\right).
\]

Two related dimensionless values are reported:

\[
\mathcal R_{\rm radius}^{\rm proxy}=\frac{L}{r_{\rm reach}^{\rm proxy}},
\qquad
\mathcal R_{D}^{\rm proxy}=\frac{L}{2r_{\rm reach}^{\rm proxy}}.
\]

The second follows the existing SST `length_over_diameter` convention.

`writhe_midpoint_proxy` and `acn_midpoint_proxy` use midpoint quadrature of the Gauss double integral. They require resolution convergence before interpretation.

## Dynamic order

After Kabsch alignment to the reference frame,

\[
\epsilon_{\rm shape}(t)=\frac{\mathrm{RMSD}(t)}{R_g(0)},
\qquad
Q_{\rm geom}(t)=\exp[-\epsilon_{\rm shape}(t)^2].
\]

This `Q_geom` is a declared diagnostic convention, not a universal topological invariant.

When a material phase field is supplied,

\[
Q_{\rm phase}(t)=
\left|\frac{1}{N}\sum_j
\exp\{i[\vartheta_j(t)-\vartheta_j(0)]\}\right|.
\]

The approximate incompressible Falk--Langer residual uses an unconstrained local affine fit followed by singular-value rescaling to unit determinant. It is therefore labelled `projected_det1`, not an exact constrained minimizer.


## Dynamic spectrum

For uniformly sampled times, the package Fourier transforms the spatial phase modes in time and reports, for each integer mode \(m\),

\[
k_m=\frac{2\pi m}{L},\qquad
\omega_m=2\pi f_{\rm peak}(m).
\]

A log--log fit provides \(\omega=A k^p\). The reported half-FWHM quantity is a `damping_proxy`; it is not automatically a pole damping rate and requires window-, duration-, and resolution-convergence tests.
