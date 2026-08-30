# SST QHP Stability Landscape Blind Falsifier v0.1.2

Purpose: determine whether a KnotPlot QHP geometry sweep contains a **vortex-dynamical restoring fixed point**, rather than merely a geometric/ropelength optimum.

## Primary observable
For each aligned, arclength-resampled QHP geometry \(\mathbf X(q,h,p)\), compute the regularized finite-core Biot--Savart velocity \(\mathbf U\), remove tangential/reparameterization velocity, estimate local QHP-manifold tangent fields \(\partial_q\mathbf X,\partial_h\mathbf X,\partial_p\mathbf X\), and solve the Gram projection

\[
\mathbf U_\perp \approx F_q\partial_q\mathbf X+F_h\partial_h\mathbf X+F_p\partial_p\mathbf X.
\]

A candidate fixed point satisfies \(\|F\|\approx0\). A local 3D restoring point additionally requires the Jacobian

\[
J_{ij}=\frac{\partial F_i}{\partial \xi_j},\qquad \xi=(q,h,p),
\]

to have \(\max\Re\lambda(J)<0\). For one-dimensional Q/H/P slices, a zero crossing is restoring when \(dF_\xi/d\xi<0\).

## Why this is stronger than an Rg-only landscape
A radius-of-gyration drift can miss a shape-restoring flow or mistake anisotropic deformation for collapse/expansion. The QHP projection asks whether the actual Euler/Biot--Savart motion points back along the **same geometric degrees of freedom used to generate the sweep**.

## Input
Place a `qhp_metadata.csv` in the QHP sweep root:

```csv
file,family,q,h,p,replicate
relative/path/to/geometry.txt,3.1,0.0,0.0,0.0,0
```

v0.1.1 first attempts strict filename inference automatically. If every XYZ filename contains explicit `q`, `h`, and `p` tokens, `run_all*.cmd` promotes them to `qhp_metadata.csv` and continues. If not, it creates `qhp_metadata_template.csv` and stops before physics.

To generate/refresh the template manually, run:

```bat
run_metadata_template.cmd C:\path\to\QHP\sweep
```

Fill q/h/p and rename/copy the template to `qhp_metadata.csv`. Geometry text files need at least 16 rows containing XYZ numbers. Replicates are kept on separate neighbor chains via the `replicate` column.

By default each geometry is centered and normalized to unit radius of gyration before the QHP manifold is built (`normalize_geometry_scale=true`). This isolates **shape** stability. Set it to `false` only when absolute scale is itself a physically intended Q/H/P degree of freedom.


## Metadata integrity and geometry gate

v0.1.2 treats the QHP generator metadata as part of the preregistered numerical gate:

- rows with `geometry_ok=false` are excluded **before** blind preparation and Biot--Savart evaluation;
- duplicate geometry file paths are a hard error;
- duplicate `(family, replicate, q, h, p)` manifold nodes are a hard error because finite-difference tangents would be ambiguous;
- `prepare_summary.json` reports total metadata rows and the number excluded by the geometry gate.

Use **SST KnotPlot QHP Sweep Generator v0.1.1 or newer** when different source seeds can share a numeric topology class. The unique family identities (`knot_6.3`, `link_6.3.1`, etc.) prevent unrelated centerlines from being mixed into one QHP manifold.

## One-click runs

```bat
run_all.cmd C:\path\to\QHP\sweep
run_all_extended.cmd C:\path\to\QHP\sweep
```

The default dataset path is `..\..\KnotPlot\qhp`; passing the actual QHP directory is recommended.

`run_all_extended.cmd` also runs N=64/96/128 resolution checks.

## Blind discipline
The worker receives anonymous candidate/family IDs plus numerical QHP coordinates. It does **not** receive physical filenames or family names until reveal. QHP coordinates cannot be hidden because they are the independent variables of the stability landscape.

## Gates
- consistent QHP manifold tangents;
- finite projection fraction (motion must actually live partly on the sampled QHP manifold);
- instantaneous zero crossing with negative slope;
- independent short-time RK4 projection with the same restoring sign;
- for full 3D grid points: negative real parts of all local Jacobian eigenvalues;
- local affine solve `xi* = xi0 - J^{-1} F0` with the root constrained to the neighboring QHP cell;
- short-time diagonal restoring slopes must also be negative for an affine fixed-point confirmation;
- resolution convergence in extended mode.

A PASS is only a **numerical candidate restoring structure on the sampled finite-core model**. It is not proof that the knot is a stable Euler solution, and not evidence for SST ontology by itself.

## Relation to the Breathing--Stretching--Return-Phase campaign
The previous `final`-knot campaign found collapse, expansion and near-reversal classes but no complete packet return in its short time window. QHP Stability Landscape deliberately asks an earlier mechanistic question: **where is the dynamical equilibrium manifold?** A later return-phase experiment should be launched around a certified restoring QHP point rather than around an arbitrary geometric relaxed representative.

## Windows/MSVC portability
The pybind11 kernel uses `py::ssize_t`, never a global `ssize_t`, to avoid the MSVC failure seen in the earlier v0.1.0 build.
