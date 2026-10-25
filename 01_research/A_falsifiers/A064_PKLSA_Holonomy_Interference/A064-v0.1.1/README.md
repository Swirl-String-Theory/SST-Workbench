# A064 - PKLSA Flow Separatrix & Material Transport v0.1.1

**Self-contained model-snapshot prototype** - **NOT** certified with framework v1.0.7; **NOT** physical PKLSA Euler dynamics. Scientific separatrix inference remains `UNRESOLVED`.

## One-click Windows use

Unzip the full `A064-v0.1.1_SELF_CONTAINED.zip` anywhere on Windows (no Drive or internet *data* dependency). Python dependencies are installed once on first launch (requires pip / internet for package installation if not cached). Run:

```bat
run_all.cmd                 rem analyze three shipped model NPZs and write a PDF
run_all.cmd SELFTEST        rem scientific/software regression tests
run_all.cmd BUILD_NPZ       rem verify/rebuild NPZ inputs from included XYZ knots
run_all.cmd BUILD_NPZ --force  rem regenerate all three datasets
run_all.cmd SNAPSHOTS --source data\MODEL_NPZ\PKLSA_3_1_stationary_BS_DEMO.npz
```

Alternately the individual scripts `run_01_build_npz.cmd` and `run_02_bundled.cmd` work. Linux: `pip install -r requirements.txt && python -m a064.cli BUNDLED`.

**Data input is already included.** No separate `.npz` download, PKLSA installation or Google Drive access is needed. `BUILD_NPZ` is implemented inside `a064/build_npz.py`, not a stub.

## Exactly what is generated

- `data/MODEL_NPZ/PKLSA_3_1_stationary_BS_DEMO.npz`
- `data/MODEL_NPZ/PKLSA_5_2_stationary_BS_DEMO.npz`
- `data/MODEL_NPZ/PKLSA_6_1_stationary_BS_DEMO.npz`
- Every `.npz` has a `.source.json` recording the raw geometry SHA-256, parameters, numerical shape, evidential status and NPZ SHA-256.

Each NPZ contains `x,y,z` in **meters**, `t` in **seconds**, `v` in **meters/second**, array shape `(nt,nx,ny,nz,3)`, and `source_type` plus `time_model` metadata. The shipped datasets have three **identical** velocity frames and grid 31^3. The source is direct KnotPlot-native XYZ imported via Drive, **not a certified E011 provider-anchor realization**.

Mathematical model (midpoint-segment regularized Biot-Savart):

$$
\mathbf v(\mathbf x)\approx\frac{\Gamma}{4\pi}\sum_j\frac{\Delta\boldsymbol\ell_j\times (\mathbf x-\mathbf X_j)}{(|\mathbf x-\mathbf X_j|^2+a^2)^{3/2}}
$$

where `a=core_m`, `Gamma=gamma_m2_s`, source XYZ points are scaled using `scale_m_per_unit`. Default **demonstration-only** values: `scale_m_per_unit=1 m/native-unit`, `core_m=0.8 m`, `gamma_m2_s=10 m^2/s`, time stamps `0, 0.07, 0.14 s`. These values are **artificial**, not the SST canon or PKLSA measurement calibration. The frozen repeated frames **cannot** demonstrate time-dependent Euler dynamics, stationarity, a material vortex tube or a physical separatrix.

## Build from your own calibrated PKLSA geometry

All 3 scale parameters must be given together if any is set:

```bat
run_all.cmd BUILD_NPZ --knot 3_1 --scale-m-per-unit 1.40897017e-15 --core-m 1.40897017e-15 --gamma-m2-s 9.6836192e-9 --grid 31 --force
```

This is a user-specified scale example only. It does not verify what length the original native coordinates represent. For a different XYZ file use:

```bat
run_all.cmd BUILD_NPZ --source C:\data\my_PKLSA_xyz.txt --output-npz C:\data\my_PKLSA_model.npz --scale-m-per-unit 1e-15 --core-m 1e-15 --gamma-m2-s 1e-8 --grid 31
run_all.cmd SNAPSHOTS --source C:\data\my_PKLSA_model.npz
```

The `SNAPSHOTS` command reads model `.source.json` and **never promotes** such a file to independent flow evidence. A tampered sidecar SHA-256 causes a hard error.

## Scientific procedure and limitations

1. **Discovery (transport blind):** extract closed candidate surfaces from a preregistered enstrophy isosurface sweep of the supplied velocity. Hyperbolic stagnation checks are independent complementary discovery.
2. **Transport:** freeze candidate, compute its normal relative velocity, symmetric tracer crossing statistics and RK4 refinement.
3. **Unresolved:** certify Lagrangian manifold identity, grid/time refinement, true time evolution, source-provider independence, incompressible Euler residuals, and independent C++ FP64 verification; framework v1.0.7 has not generated a valid FREEZE/CERTIFY ledger.

A physical claim **requires actual 3D Euler velocity snapshots**, or independently validated measured 3D fields, for *the same* PKLSA carrier plus a source-qualification manifest. Source index and scientific constraints: `README_v0.1.0.md`, `docs/THEORY.tex`, `configs/BLIND_PROTOCOL.json`. For geometric qualification, use E010-v0.3.1 and E011-v0.3.0 on the authoritative Workbench instead of relabeling raw XYZ data.

## Outputs

- `A064_PKLSA_Flow_Separatrix_Transport_v0.1.1-outputs/pklsa_*_npz/{CANDIDATE_DISCOVERY.json,DISCOVERY_SEAL.sha256,CANDIDATE_SURFACE.npz,GATE_RESULTS.json}`
- `A064-v0.1.1_FALSIFIER_REPORT.pdf`
- `A064_PKLSA_Flow_Separatrix_Transport_v0.1.1-outputs_PROTOTYPE.zip` (not an official blind/reveal seal).

Do not treat absence of vorticity surfaces as proof of absence of separatrices; irrotational hyperbolic stagnation controls are part of the test suite.