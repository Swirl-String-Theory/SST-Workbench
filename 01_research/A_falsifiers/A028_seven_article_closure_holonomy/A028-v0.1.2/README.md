# SST Seven-Article Closure & Holonomy Blind Falsifier v0.1.2

Purpose: convert the seven-paper review into a **blind, non-promotional** SST audit suite.
The package distinguishes exact fluid identities, research bridges, representation effects, and genuinely SST-specific hypotheses.

## Core scientific rule
A successful numerical run is **not** evidence for SST by itself. A gate is allowed to return:

- `PASS` — the preregistered test was available and passed;
- `FAIL` — an available hard test failed;
- `INDETERMINATE` — required physical data were absent or the observable was not identifiable;
- `REFERENCE_ONLY` — diagnostic/null calculation, not an SST theorem test.

Static KnotPlot/Ridgerunner centerlines cannot by themselves prove pressure, vorticity-core, phase-fiber, metric, or clock claims. The suite therefore refuses to infer those fields from centerline geometry.

## Default real-data path

```text
..\..\KnotPlot\knots\final
```

Override by passing a path to the CMD script.

## Turn-key Windows runs

```bat
run_all.cmd
run_all_extended.cmd

rem strict two-stage blind workflow
run_blind_only.cmd
run_blind_extended_only.cmd
run_reveal.cmd results\basic
```

or

```bat
run_all.cmd C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

The scripts:
1. create `.venv`;
2. install NumPy + pybind11;
3. build the C++17 native extension;
4. run Python/native parity selftests;
5. create a SHA-256 committed blind case set;
6. run BASIC or EXTENDED gates using opaque case IDs;
7. freeze results before reveal;
8. reveal source filenames only after scoring.

## v0.1.2 integrity corrections

- multi-component text links are preserved instead of concatenated;
- conservative validated jump segmentation recovers legacy concatenated link exports;
- G03 now actually evaluates pairwise Gauss linking for recovered components and reports raw/resampled quadrature;
- `opaque_results.json` is written as exact UTF-8/LF bytes and the freeze hashes those bytes; reveal refuses to proceed on a freeze mismatch;
- the private mapping commitment is likewise byte-stable and verified before reveal;
- BASIC and EXTENDED reuse one private random blind state for an unchanged dataset snapshot, giving identical opaque IDs and train/holdout assignments;
- byte-identical files at different relative paths no longer collide on case IDs.

Use `run_all_both.cmd` to run BASIC and EXTENDED and automatically verify that their manifests match. Delete `results\_blind_state` only when you intentionally want a fresh blind randomisation.

## Seven source-derived gate families

| Article | Transfer to SST audit | Promotion status |
|---|---|---|
| 1. *Observation of conformal field theory spectra in a quantum simulator* | finite-size spectral convergence, symmetry/boundary-sector filtering, dynamical-spectrum discipline | protocol only; no CFT ratios imposed on SST |
| 2. *Acoustic toroidal vortices with programmable links and knots* | centerline/vorticity/phase-fiber topology separation; integer winding/connectivity tests | research-track guard |
| 3. *A source-term interpretation of turbulent rough wall-pressure spectra* | exact incompressible pressure-Poisson source ledger and Green reconstruction | orthodox identity; strongest canon candidate |
| 4. *Topologically Configurable Nonlinear Vortex Generation at van der Waals Heterostructures* | dynamic/geometric phase decomposition, winding closure, phase-pixel alias/purity nulls | research methodology |
| 5. *Wormhole Geometry from a Magnetic Vortex* | derive effective metric from probe principal symbol; even/odd circulation decomposition; finite-core collapse | conditional bridge only |
| 6. *A transport geometry of acoustic analogies* | formulation invariance, on-shell residual ledger, closed-loop representation holonomy and refinement | canon-level methodology guard |
| 7. *Late-Time Cosmic Acceleration in Hořava–Lifshitz Gravity...* | kinematics-vs-dynamics guard; domain/pole/asymptotic/derived-quantity reproduction | canon-level inference guard |

## Input schemas

### 1. Static centerline
Recognized coordinate files: `.txt`, `.xyz`, `.csv`, `.dat`, `.vect`.
Simple files must contain at least three numeric columns per coordinate row. Multi-component TXT/XYZ/CSV/DAT files may separate closed components with blank lines or component-marker lines. v0.1.2 also has a conservative jump fallback: a split is accepted only when every candidate segment is independently well closed; the parser method is recorded in the blind manifest and G00.

### 2. Optional phase sidecar
Next to `knot.txt` place `knot.phase.npy` (1-D phase in radians). The phase gates measure closed-loop winding, modal purity, and whether the dominant winding remains fixed under sampling refinement rather than following a discretization alias.

### 3. Optional Euler field sidecar
`knot.field.npz` with:

```python
v         # shape (Nx,Ny,Nz,3), SI velocity
p         # shape (Nx,Ny,Nz), SI pressure
dx        # scalar or length-3 spacing
rho_f     # optional scalar; defaults to 7.0e-7 kg m^-3
boundary  # optional string; 'periodic' enables FFT Green closure
```

The exact tested identity is

```text
∇²(p/rho_f) = 1/2 |omega|² - S_ij S_ij
```

for constant-density incompressible Euler flow.

### 4. Optional time-series sidecar
`knot.timeseries.npz` with `t` and `signals`. `signals` may be `(T,)`, `(runs,T)`, or `(runs,T,channels)`.
Optional `L` provides a characteristic length per run for the Article-1-inspired finite-size collapse diagnostic. When `L` is present, raw frequency drift is treated as descriptive and the hard gate is the collapse of the scaled frequency `f*L`.

### 5. Optional sign-reversal/probe sidecar
`knot.probe_pair.npz` with arrays `plus` and `minus`, produced from identical experiments/simulations under reversed circulation. The package decomposes

```text
O_even = (O_plus + O_minus)/2
O_odd  = (O_plus - O_minus)/2
```

It does **not** call either component “gravity” automatically.

### 6. Optional representation sidecar
`knot.repr.npz` with `A`, `B`, optional `residual`, optional `eps`, `AB`, `BA`.
This tests whether supposedly equivalent formulations agree on the observable. Optional `AB_seq`, `BA_seq`, and `eps_seq` arrays activate the commutator/refinement gate, which checks convergence of `||AB-BA||/eps^2`.

## Gate catalogue

| Gate | Role | Hard when data exist? |
|---|---|---|
| `G00` | coordinate integrity / closure gap | yes |
| `G01` | resampling and low-mode convergence | yes |
| `G02` | topology-layer non-equivalence | reference guard |
| `G03` | centerline Gauss linking | reference only |
| `G10` | integer phase closure | yes |
| `G11` | phase sampling/alias stability | yes |
| `G20` | pressure-Poisson closure | yes |
| `G21` | periodic Green reconstruction | yes |
| `G22` | enstrophy/strain pressure-source ledger | reference only |
| `G30` | repeated-run spectral stability | yes when `L` absent |
| `G31` | finite-size `f L` collapse | yes when `L` present |
| `G40` | even/odd circulation-reversal decomposition | classifier only |
| `G50` | representation invariance | yes |
| `G51` | commutator/refinement convergence | yes when sequence arrays exist |

## Output

`results/<run>/` contains:
- `blind/public_manifest.json`
- `blind/private_mapping.json` (not used in scoring output)
- `preregistration.json`
- `opaque_results.json`
- `summary_blind.md`
- after reveal: `revealed_results.json`, `summary_revealed.md`

## Scientific non-equivalences frozen by this release

```text
centerline knot != phase-fiber knot
phase singularity != material vorticity core
large |omega| != automatically local pressure minimum
closed topology != dynamical stability
probe effective metric != curvature of the substrate space
kinematic H(z) fit != derivation of gravity dynamics
finite-step representation holonomy != physical clock holonomy
```

See `THEORY_MAP.md` and `canon_patch/`.
