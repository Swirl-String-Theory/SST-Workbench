# SST-21D Knot Order Pipeline v0.1.0

Self-contained Python + C++ research harness for extending an SST-21 knot-topology catalogue with independently separated:

1. **topological identity/provenance**;
2. **geometric realization diagnostics**;
3. **phase/dynamical-order diagnostics**;
4. **epistemic and numerical certification fields**.

The primary input is Brian Gilbert's `ideal_favorites.txt`/`ideal.txt` Fourier catalogue. Every `AB` entry receives a geometry row. Additional SST-21 semantic columns are merged from the editable `data/sst21_metadata_seed.csv`; unverified or absent metadata remains blank rather than being inferred.

The package also ingests KnotPlot plain XYZ files and Ridgerunner-polished TXT/VECT outputs.

## Scientific boundary

A static Fourier curve can determine geometric diagnostics, but it cannot determine a dynamical phase order. Therefore static rows deliberately contain

```text
dynamic_status = NOT_MEASURED_REQUIRES_TRAJECTORY
```

and leave `Q_phase`, `Dmin`, dispersion, damping, and defect-percolation fields empty. A catalogue label is treated as provenance, not as an independently recomputed knot certificate.

The package reports a **sampled reach/DCSD proxy**, not an exact thickness certificate. The midpoint Gauss sums are convergence diagnostics, not exact polygonal writhe/linking algorithms. KnotPlot `safe`, `lnknum`, and Ridgerunner residual sidecars can be merged when present.

## Natural SST normalization

The bundled default constants are

```text
v_swirl = 1.09384563e6 m s^-1
r_c     = 1.40897017e-15 m
```

so the natural core-transit time is

\[
t_c=\frac{r_c}{\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}}
   =1.28810124\times 10^{-21}\ \mathrm{s}.
\]

No CODATA mass, Newton constant, or Planck length is used by the geometry pipeline.

## Folder layout

```text
cpp/                    C++17 shared-library accelerator (ctypes, no pybind11)
sst21d/                 Python package
scripts/                convenience entry points
examples/               mini Fourier catalogue and dynamic demo generator
data/                    editable SST-21 metadata seed and database placeholder
docs/                    schema and formulas
tests/                   smoke and parity tests
```

## Windows quick start

Copy your database to:

```text
data\ideal_favorites.txt
```

Then run:

```bat
RUN_BUILD_NATIVE.bat
RUN_STATIC_FAVORITES.bat
RUN_CONVERGENCE_FAVORITES.bat
```

Outputs appear under `outputs\static_favorites`:

```text
sst21d_master.csv
sst21d_master.json
manifest.json
geometry\*.json
```

## Equivalent commands

```powershell
py -3 -m pip install -e . --no-build-isolation
py -3 -m sst21d build-native
py -3 -m sst21d static --database data\ideal_favorites.txt --samples 600 --metadata data\sst21_metadata_seed.csv --out outputs\static_favorites --require-native
```

Resolution convergence campaign:

```powershell
py -3 -m sst21d convergence --database data\ideal_favorites.txt --resolutions 128 256 512 --out outputs\convergence_favorites --require-native
```

List catalogue entries:

```powershell
py -3 -m sst21d list --database data\ideal_favorites.txt
```

Export selected Fourier entries for KnotPlot/Ridgerunner:

```powershell
py -3 -m sst21d export --database data\ideal_favorites.txt --ids 3:1:1 4:1:1 5:1:2 --samples 300 --format both --out exports\favorites
```

Analyze an existing KnotPlot/Ridgerunner folder:

```powershell
py -3 -m sst21d analyze-xyz --input C:\workspace\projects\SST-Workbench\KnotPlot\knots --glob "**/*_polish.txt" --samples 300 --out outputs\ridgerunner
```

Create a bridge BAT that calls your existing `run_three_stage.cmd` and then analyzes its output folder:

```powershell
py -3 -m sst21d make-rr-bridge --pipeline-cmd C:\workspace\projects\SST-Workbench\KnotPlot\ridgerunner\run_three_stage.cmd --out RUN_EXISTING_RIDGERUNNER_AND_ANALYZE.bat
```

## Dynamic trajectory format

Use an NPZ file containing:

```text
points : float64 array, shape (T,N,3) or (T,C,N,3)
times  : optional float64 array, shape (T,)
phase  : optional float64 array, shape (T,N) or (T,C,N), radians
```

Then:

```powershell
py -3 -m sst21d dynamic --trajectory trajectory.npz --topology-key 3_1 --time-unit s --length-unit m --out outputs\dynamic
```

The command also writes `dynamic_master_row.csv`, keyed by `topology_key`, for joining to the static SST-21D table.

The dynamic analyzer computes rigid-aligned shape overlap, normalized RMSD, an approximate volume-preserving Falk--Langer residual, optional phase order, phase structure factors, defect-cluster fractions, and an empirical mode-dispersion table with spectral-width/damping proxies.

## KnotPlot/Ridgerunner compatibility

If CMake is unavailable, set `SST21D_CXX` (for example to the Strawberry `c++.EXE` path); the builder then compiles the shared library directly.

KnotPlot TXT is parsed as one `x y z` vertex per line with blank lines separating components. VECT export uses closed plCurve/Geomview polylines. This matches the existing SST workflow:

```text
KnotPlot checkpoint selection
    -> one selected TXT seed
    -> three-stage Ridgerunner
    -> polished TXT/VECT
    -> SST-21D analysis
```

The package does **not** rerun Ridgerunner on a VortexLab uniform-resampled derivative. The polished audit geometry remains the authoritative geometry; resampling is used only for diagnostics.

## Gates

Static rows report independent gates:

```text
G0_PARSE
G1_FINITE
G2_EDGE_UNIFORMITY
G3_POSITIVE_REACH_PROXY
G4_SOURCE_LENGTH_CONSISTENCY
G5_NATIVE_BACKEND_AVAILABLE
G6_TOPOLOGY_SIDECAR_PRESENT
G7_RIDGERUNNER_RESIDUAL_PRESENT
G8_DYNAMIC_TRAJECTORY_PRESENT
G9_PHASE_FIELD_PRESENT
G10_CONVERGENCE_CERTIFIED
```

No single pass flag is promoted to a particle identification.

## Tests

```powershell
py -3 -m pytest
```

See `docs/SCHEMA.md`, `docs/METHODS.md`, and `REFERENCES.tex` for definitions and provenance.
