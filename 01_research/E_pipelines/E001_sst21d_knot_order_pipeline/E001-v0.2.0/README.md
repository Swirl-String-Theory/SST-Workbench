# SST-21D Knot Order Pipeline v0.2.0

Self-contained Python + C++17 research harness for extending an SST-21 knot-topology catalogue with independently separated:

1. topological identity and provenance;
2. geometric realization diagnostics;
3. phase/dynamical-order diagnostics;
4. numerical and epistemic certification fields.

Version 0.2.0 supports three static source families:

- Brian Gilbert `ideal_favorites.txt` / `ideal.txt` XML-style Fourier catalogues;
- legacy six-column `.fseries` Fourier files;
- legacy three-column `.short` polygon files.

The supplied `data/Fresnel_FourierSeries.zip` is ready to process. It contains 78 `.fseries` files, 76 `.short` files, 73 exact representation pairs, five Fourier-only variants, and three polygon-only variants.

## Critical `.fseries` indexing issue

The lexical difference between `0.000`, `0.000000`, and similar zero tokens is harmless: all are parsed as the same floating-point zero, while their original token styles remain recorded for provenance.

The real ambiguity is the implicit Fourier index. A six-column row stores

```text
a_x(j) b_x(j) a_y(j) b_y(j) a_z(j) b_z(j)
```

but some files include an explicit `j=0` row, whereas others begin immediately at `j=1`. An all-zero first row is not sufficient to decide this, because symmetry can also make the genuine `j=1` row vanish.

The package therefore tests both candidates,

\[
\mathbf X_\nu(t)=\sum_{r=0}^{M-1}
\left[\mathbf A_r\cos((r+\nu)t)+\mathbf B_r\sin((r+\nu)t)\right],
\qquad \nu\in\{0,1\},
\]

and, where a matching `.short` file exists, chooses the index origin with the lowest closed-curve Procrustes discrepancy after translation, scale, rigid rotation, cyclic phase shift, and parameter reversal are removed.

Every Fourier row reports:

```text
harmonic_origin
origin_method
origin_status
origin_fit_rmsd_j0
origin_fit_rmsd_j1
origin_confidence_ratio
```

All 78 Fourier files in the supplied archive are resolved explicitly. Manual exceptions can be entered in `data/fseries_origin_overrides.csv`.

## Scientific boundary

A static curve can determine geometric diagnostics, but it cannot determine dynamical phase order. Static rows therefore contain

```text
dynamic_status = NOT_MEASURED_REQUIRES_TRAJECTORY
```

and leave `Q_phase`, `Dmin`, dispersion, damping, defect percolation, and lifetime fields empty. Directory and filename labels are treated as provenance, not as independently recomputed knot certificates.

The package reports sampled reach/DCSD and midpoint Gauss-integral proxies. These require resolution convergence and do not replace strict Ridgerunner thickness/residual certification.

## Windows quick start for `.fseries` and `.short`

Run the complete normal campaign:

```bat
RUN_FRESNEL_ALL.cmd
```

Run the high-resolution campaign, including both representation convergence campaigns:

```bat
RUN_FRESNEL_ALL_MAX.cmd
```

Individual stages:

```bat
RUN_FRESNEL_SCAN.bat
RUN_FRESNEL_STATIC.bat
RUN_FRESNEL_EXPORT_RIDGERUNNER.bat
```

The main outputs are:

```text
outputs\fresnel_scan\fresnel_inventory.csv
outputs\fresnel_static\sst21d_fresnel_master.csv
outputs\fresnel_static\fresnel_representations.csv
outputs\fresnel_static\geometry\*.json
exports\fresnel_ridgerunner\<topology>\*.txt
exports\fresnel_ridgerunner\<topology>\*.vect
```

`sst21d_fresnel_master.csv` contains one row per variant pair and selects `.short` as the primary geometry when available. `fresnel_representations.csv` preserves independent metrics for every `.fseries` and `.short` representation.

## Equivalent commands

Install and build the C++ accelerator:

```powershell
py -3 -m pip install -e . --no-build-isolation
py -3 -m sst21d build-native
```

Inventory and index-origin audit:

```powershell
py -3 -m sst21d fresnel-scan --input data\Fresnel_FourierSeries.zip --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_scan
```

Full static SST-21D table:

```powershell
py -3 -m sst21d fresnel-static --input data\Fresnel_FourierSeries.zip --samples 600 --prefer short --metadata data\sst21_metadata_seed.csv --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_static --require-native
```

Fourier convergence:

```powershell
py -3 -m sst21d fresnel-convergence --input data\Fresnel_FourierSeries.zip --representation fseries --resolutions 128 256 512 1024 --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_convergence_fseries --require-native
```

`.short` convergence:

```powershell
py -3 -m sst21d fresnel-convergence --input data\Fresnel_FourierSeries.zip --representation short --resolutions 128 256 512 1024 --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_convergence_short --require-native
```

Export all variants for KnotPlot/Ridgerunner:

```powershell
py -3 -m sst21d fresnel-export --input data\Fresnel_FourierSeries.zip --samples 400 --representation short --format both --origin-overrides data\fseries_origin_overrides.csv --out exports\fresnel_ridgerunner
```

If the requested representation is absent, export falls back to the representation that exists.

## `ideal_favorites.txt` route

Copy the database to `data\ideal_favorites.txt`, then run:

```bat
RUN_BUILD_NATIVE.bat
RUN_STATIC_FAVORITES.bat
RUN_CONVERGENCE_FAVORITES.bat
```

Equivalent command:

```powershell
py -3 -m sst21d static --database data\ideal_favorites.txt --samples 600 --metadata data\sst21_metadata_seed.csv --out outputs\static_favorites --require-native
```

## KnotPlot/Ridgerunner integration

The package exports plain XYZ and closed Geomview/plCurve VECT files. It deliberately delegates relaxation to the user's existing tested KnotPlot → three-stage Ridgerunner pipeline.

A bridge script can still be generated:

```powershell
py -3 -m sst21d make-rr-bridge --pipeline-cmd C:\workspace\projects\SST-Workbench\KnotPlot\ridgerunner\run_three_stage.cmd --out RUN_EXISTING_RIDGERUNNER_AND_ANALYZE.bat
```

Analyze polished outputs:

```powershell
py -3 -m sst21d analyze-xyz --input C:\workspace\projects\SST-Workbench\KnotPlot\knots --glob "**/*_polish.txt" --samples 300 --out outputs\ridgerunner
```

## Dynamic trajectory route

An NPZ trajectory may contain:

```text
points : shape (T,N,3) or (T,C,N,3)
times  : optional shape (T,)
phase  : optional shape (T,N) or (T,C,N), radians
```

Run:

```powershell
py -3 -m sst21d dynamic --trajectory trajectory.npz --topology-key 3_1 --time-unit s --length-unit m --out outputs\dynamic
```

## Natural SST normalization

The bundled default constants are

```text
v_swirl = 1.09384563e6 m s^-1
r_c     = 1.40897017e-15 m
```

so

\[
t_c=\frac{r_c}{\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}}
=1.28810124\times10^{-21}\ \mathrm{s}.
\]

## Tests

```powershell
py -3 -m pytest
```

The test suite includes both `0.000` and `0.000000` token styles, explicit `j=0`, implicit `j=1`, an all-zero genuine first harmonic, `.short` parsing, and a full bundled-archive inventory test.

See `docs/SCHEMA.md`, `docs/METHODS.md`, `VALIDATION.md`, and `REFERENCES.tex`.
