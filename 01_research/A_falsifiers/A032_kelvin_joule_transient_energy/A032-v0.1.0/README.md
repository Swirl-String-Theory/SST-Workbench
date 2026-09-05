# Kelvin–Joule SST Transient Energy Falsifier v0.1.0

GPU-first blind falsifier for relaxed SST knot centerlines, built from the **SST_GPU_SYCL_DPC_audit_template** architecture.

The package implements the proposed research track:

> **Kelvin–Joule Transient Energy Closure, Ringdown and Constriction Null Gates**

with a persistent SYCL/DPC++ queue, Intel Arc / Level Zero support, OpenMP fallback, and a small pure-Python parity path.

## What is tested

The campaign is deliberately target-blind. Source file names/topology labels are removed before the dynamical analysis and restored only after all metrics and PASS/FAIL decisions have been written.

| Gate | Implemented test |
|---|---|
| `KJ-G0` | Frozen protocol hash + blind source-ID manifest |
| `KJ-G1` | Baseline Kelvin-impulse conservation diagnostic |
| `KJ-G2` | Regularized filament Hamiltonian no-loss / energy closure |
| `KJ-G3` | `+epsilon / -epsilon` ringdown-frequency symmetry when a frequency is resolved |
| `KJ-G4` | Kelvin-duration-like integral support time, including window-dependence classification |
| `KJ-G5` | Synthetic incompressible constriction/Bernoulli null + constriction-release no-loss |
| `KJ-G6` | Resolution-ladder convergence of energy drift and resolved ringdown frequency |

No fit to `alpha`, particle masses, `G`, or a topology-specific target is performed.

## Canonical SST constants

The workbench uses the supplied canonical values directly:

```text
v_swirl       = 1.09384563e6 m s^-1
r_c           = 1.40897017e-15 m
rho_core      = 3.8934358266918687e18 kg m^-3
rho_f         = 7.0e-7 kg m^-3
Gamma_canon   = 2*pi*r_c*v_swirl
Tau_c         = r_c/v_swirl
```

The input relaxed-knot coordinates are normally dimensionless. For each resolution, v0.1.0 rescales the curve so that one half of the minimum nonadjacent point-distance proxy equals `r_c`. That physicalization is an **explicit research assumption**, not a Canon identity. The applied scale factor is written to every output row.

## Dynamical model

The hot kernel is the Rosenhead–Moore-type regularized midpoint filament law

\[
\mathbf v(\mathbf x)=\frac{\Gamma}{4\pi}\sum_s
\frac{\Delta\boldsymbol\ell_s\times(\mathbf x-\mathbf m_s)}
{\left(|\mathbf x-\mathbf m_s|^2+r_c^2\right)^{3/2}}.
\]

The matching regularized filament Hamiltonian proxy is

\[
H_a=\frac{\rho_{\!f}\Gamma^2}{8\pi}
\sum_{i,j}
\frac{\Delta\boldsymbol\ell_i\cdot\Delta\boldsymbol\ell_j}
{\sqrt{|\mathbf m_i-\mathbf m_j|^2+r_c^2}}.
\]

The Kelvin impulse diagnostic is

\[
\mathbf I=\frac{\rho_{\!f}\Gamma}{2}
\sum_i \mathbf x_i\times\mathbf x_{i+1}.
\]

The implemented Kelvin-duration-like observable uses the nonnegative modal intensity `S(t)=a(t)^2`:

\[
T_K=\frac{\left[\int S(t)\,dt\right]^2}{\int S(t)^2\,dt}.
\]

For a pure envelope `a(t)=a_0 exp(-gamma t)`, this tends to `T_K = 1/gamma`. For an undamped persistent response it grows with the observation window; that is reported as `PERSISTENT_OR_UNRESOLVED`, not misclassified as dissipation.

See `docs/model_notes.md` for the exact scope and limitations.

## Important scientific limitation

`KJ-G2` is a no-loss gate for the implemented **regularized filament Hamiltonian**. It is not yet a complete three-dimensional incompressible-Euler pressure-Poisson closure proof. v0.1.0 does not claim to calculate the full pressure energy-flux integral on an enclosing surface.

That distinction is intentional: a failed filament energy ledger is already sufficient to reject a numerical run; a passed ledger is necessary but not sufficient evidence for full Euler closure.

## Input dataset

Default path, matching the SST Workbench layout:

```text
..\..\KnotPlot\knots\final
```

Recognized sampled centerline formats:

```text
.txt  .xyz  .csv  .dat  .pts  .vect  .npy  .json
```

Files that cannot be interpreted as finite `N x 3` centerlines are listed in `skipped_files.json`; they are never silently coerced.

A raw Fourier coefficient `.fseries` file is deliberately **not** guessed as XYZ data. Use its sampled centerline companion for this v0.1.0 workbench.

## Windows quick start

### One command, install + smoke + basic + extended

```bat
run_all.cmd
```

This uses the default dataset path above and backend `auto`.

Explicit dataset:

```bat
run_all.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

Explicit backend:

```bat
run_all.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final" openmp
```

### Individual stages

```bat
run_install.cmd
run_smoke.cmd
run_basic.cmd
run_extended.cmd
```

`run_basic.cmd` defaults to one resolution (`N=128`) with a deterministic `+/- 0.03 r_c` perturbation pair and a constriction-release test.

`run_extended.cmd` uses the resolution ladder `128, 256, 512`, multiple normal/binormal perturbations, longer transients, stricter tolerances, and `KJ-G6` convergence checks.

## Intel Arc / oneAPI SYCL

The preferred heavy path is Intel oneAPI DPC++ with Level Zero:

```bat
run_arc.cmd
run_arc_basic.cmd
run_arc_extended.cmd
```

or everything:

```bat
run_all_arc.cmd
```

The Arc scripts load:

```text
C:\Program Files (x86)\Intel\oneAPI\setvars.bat
```

and set:

```text
ONEAPI_DEVICE_SELECTOR=level_zero:0
SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
ZES_ENABLE_SYSMAN=1
```

They fail instead of silently using a host CPU when `sycl` was explicitly requested.

## Backend ladder

1. SYCL GPU / Intel Arc (`icpx -fsycl`, Level Zero)
2. SYCL CPU only when explicitly allowed
3. native OpenMP
4. Python parity/smoke path

The extended campaign refuses an **accidental** Python fallback when `auto` was requested. Passing `--backend python` explicitly overrides that guard, but is not recommended for the heavy ladder.

## Blind protocol

`run_pipeline.py` performs three stages:

1. **Prepare** — discover/validate centerlines, replace source names with `sample_<hash>`, freeze the JSON protocol and SHA-256 hash.
2. **Run blind** — only `sample_<hash>.npy` and the public manifest are read; gates are decided here.
3. **Unblind** — source-relative names are merged into a separate final result only after the blind output exists.

Campaign output contains:

```text
frozen_protocol.json
blind_manifest.public.json
blind_manifest.private.json
results_blind.csv
results_blind.json
traces_blind.json
results_unblinded.csv
results_unblinded.json
summary.json
skipped_files.json
```

Do not inspect `blind_manifest.private.json` before `results_blind.*` is complete if you are doing a manually supervised blind campaign.

## Gate interpretation

### `KJ-G2` energy no-loss

For every baseline, perturbation, and released constriction:

\[
\epsilon_E = \max_t \frac{|H_a(t)-H_a(0)|}{|H_a(0)|}.
\]

The threshold is frozen in `configs/*.json` before the source identities are restored.

### `KJ-G3` sign symmetry

For matched `+epsilon` and `-epsilon` runs of the same mode:

\[
\delta_\omega =
\frac{|\omega_+-\omega_-|}{\max(|\omega_+|,|\omega_-|)}.
\]

A frequency is extracted from zero crossings when possible; a Hann-window FFT is used only when its dominant spectral peak carries enough power. Otherwise the response is `NA/unresolved`, not forced to PASS.

### `KJ-G4` Kelvin duration

The workbench reports `T_K` at 50%, 75%, and 100% of the observation window. A true finite ringdown should approach a stable support time; a persistent conservative oscillation normally remains window-dependent.

### `KJ-G5` constriction null

The synthetic streamtube control imposes

\[
A(x)u(x)=Q
\]

and checks that

\[
p(x)+\frac12\rho_{\!f}u(x)^2
\]

is constant to numerical precision. Separately, each knot receives a small volume-preserving affine squeeze with determinant one and is then released into the same no-loss filament dynamics.

### `KJ-G6` convergence

The extended profile compares adjacent resolutions without access to source labels. A high-resolution result fails if energy drift/frequency observables diverge beyond the frozen convergence tolerance.

## Demo and tests

A real runnable demo dataset is included; it is not an empty placeholder:

```bat
run_demo.cmd
```

It contains a sampled circle control and a sampled trefoil-shaped torus curve.

Python tests:

```bat
.venv\Scripts\python.exe -m pytest -q
```

The test suite includes:

- geometry/resampling;
- physicalization proxy;
- Python Biot–Savart and Hamiltonian finiteness;
- analytic Kelvin-duration limit;
- constriction Bernoulli null;
- blind-manifest leakage check;
- full tiny blind pipeline;
- native/Python parity when the native extension is built.

## Source basis

The research design is based on the supplied scans of:

- J. P. Joule and W. Thomson, *On the Thermal Effects of Fluids in Motion*;
- W. Thomson, *On Transient Electric Currents*.

Copy-ready bibliography entries are in `docs/references.tex`.

## Version status

`v0.1.0` is a **research-track falsifier**, not a Canon patch. Its strongest purpose is negative: if a nominally ideal relaxed-knot run loses the matching regularized Hamiltonian without an explicit loss channel, the run/model implementation fails the no-loss gate before any physical interpretation is attempted.
