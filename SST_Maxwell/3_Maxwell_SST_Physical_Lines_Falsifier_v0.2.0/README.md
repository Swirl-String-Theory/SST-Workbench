# 3_Maxwell_SST_Physical_Lines_Falsifier_v0.2.0

Prefix **`3_`** workbench for the Maxwell **On Physical Lines of Force** track.

This version extends the target-blind v0.1.0 harness so it can run directly on the relaxed KnotPlot centreline archive in:

```text
..\..\KnotPlot\knots\final
```

The heavy Biot--Savart evaluation is implemented in **C++17 + pybind11 + OpenMP**, following the supplied SST C++/pybind audit template. A pure-NumPy implementation is retained as a reference/fallback.

## What v0.2.0 actually tests

The centreline route is deliberately narrower than a resolved Euler simulation. Each knot/link is interpreted as the centreline of a regularized vortex tube. The fast kernel evaluates

\[
\mathbf u(\mathbf x)
 = \frac{\Gamma}{4\pi}
   \sum_k
   \frac{\Delta\boldsymbol\ell_k\times(\mathbf x-\mathbf x_k^{\rm mid})}
   {\left(\lVert\mathbf x-\mathbf x_k^{\rm mid}\rVert^2+a^2\right)^{3/2}},
\]

then samples cross-sections normal to the local centreline tangent and constructs the coarse-grained momentum-flux tensor

\[
R_{ij}=\rho_{\!f}\left(\langle u_i u_j\rangle-\langle u_i\rangle\langle u_j\rangle\right).
\]

For local tangent \(\mathbf t\), the blind observable is

\[
p_{\parallel}=\mathbf t^T R\mathbf t,\qquad
p_{\perp}=\frac{\operatorname{tr}R-p_{\parallel}}{2},\qquad
C_{\rm blind}=\frac{p_{\perp}-p_{\parallel}}
{\rho_{\!f}\lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\rVert^2}.
\]

The historical comparison coefficient is **not present in the blind package**. It is stored only in the separate unblind key and can be compared after the blind results are frozen.

### Mandatory geometry gates

- Ridgerunner source-quality guard from the accompanying `*.metrics.json` files.
- Positive transverse-vs-axial stress anisotropy.
- Local axisymmetry of the sampled stress tensor (reported as a diagnostic for curved/non-circular tubes; not a mandatory v0.2.0 centreline gate).
- Alignment of the least-stress principal axis with the centreline tangent.
- Regularization-core robustness on preregistered anchor knots.
- Resolution convergence on preregistered anchor knots.
- Parity-null test on a mirrored anchor geometry.

### Optional stronger closure tracks

The v0.1.0 reduced-momentum and structural-displacement-current tests are retained. If you later provide
`reduced_momentum.csv` and/or `storage_current.npz`, use `run_07_with_external_closures.cmd`.

## One-command use

From

```text
C:\workspace\projects\SST-Workbench\SST_Maxwell\3_Maxwell_SST_Physical_Lines_Falsifier_v0.2.0
```

run either:

```text
run_all_basic.cmd
```

or:

```text
run_all_extended.cmd
```

The scripts automatically use the shared SST workbench venv at:

```text
..\..\.venv
```

and the default knot directory at:

```text
..\..\KnotPlot\knots\final
```

Set these environment variables before running if desired:

```text
set KNOTS_DIR=D:\other\knot\directory
set SST_NATIVE_THREADS=16
```

## `run_*.cmd` map

| Script | Purpose |
|---|---|
| `run_00_install.cmd` | Create/use shared venv, install requirements, editable-install package, build C++/OpenMP extension, native selftest |
| `run_01_preflight.cmd` | Check knot files, metrics, Python/native backend and selected profile inputs |
| `run_02_basic.cmd` | Fast target-blind campaign on four representative geometries |
| `run_03_extended.cmd` | All `*_final.txt` geometries + high-resolution anchor convergence/core sweeps; C++ required |
| `run_04_native_benchmark.cmd` | Compare C++ and NumPy reference result/speed on a small workload |
| `run_05_python_reference.cmd` | Basic campaign using only NumPy reference kernel |
| `run_06_native_selftest.cmd` | Numerical C++ vs Python kernel equality test |
| `run_07_with_external_closures.cmd` | Extended geometry + reduced-momentum CSV + optional structural-current NPZ |
| `run_90_verify_frozen.cmd` | Verify that a blind output directory still matches its SHA-256 freeze manifest |
| `run_99_unblind.cmd` | Unblind a frozen blind report using the separate key |
| `run_all_basic.cmd` | Install → preflight → basic |
| `run_all_extended.cmd` | Install → preflight → extended |

## Output

Each blind run creates a timestamped directory under `outputs/`, for example:

```text
outputs\basic_20260813_184500\
    preregister_frozen.json
    geometry_cases.json
    geometry_verdict.json
    blind_report.json
    FROZEN_SHA256.json
```

`FROZEN_SHA256.json` is written automatically. Do not edit the result directory before unblinding.

## Blindness discipline

The blind code knows the SST input scales

\[
\rho_{\!f}=7.0\times10^{-7}\ \mathrm{kg\,m^{-3}},\quad
\lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\rVert=1.09384563\times10^6\ \mathrm{m\,s^{-1}},\quad
r_c=1.40897017\times10^{-15}\ \mathrm m,
\]

because these set the physical units of the generated surrogate field. It does **not** know the historical Maxwell comparison coefficient or the hidden SST electromagnetic prefactor target used by the reduced-momentum unblind step.

## Interpretation guard

A PASS means only that the relaxed centreline geometries are compatible with the preregistered Maxwell-inspired anisotropic-stress closure **inside this regularized Biot--Savart model class**. It does not establish a resolved finite-core Euler theorem, Maxwell's historical microscopic model, or SST itself.

For a stronger claim, replace the centreline surrogate by resolved finite-core velocity/pressure fields and re-run the tensor gates on those raw fields.
