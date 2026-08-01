# SST Horn-Torus Neumann BEM: All-Audits Package

Research-track / frozen-audit package for the Route-K horn-torus exterior Neumann Dirichlet-energy problem.

This package is **not** a canon proof of \(\chi_E=2\pi\). It is a reproducible numerical audit harness that separates

\[
\chi_K(\lambda)=\frac12\int_{\Omega_\lambda}|\nabla\phi_\lambda|^2\,d^3\xi,
\qquad
\chi_{\rm cav}(\lambda)=\pi^2\lambda,
\qquad
\chi_E^{\rm hollow}=\chi_K+\chi_{\rm cav}.
\]

The implemented Neumann ansatz is

\[
\mathbf v_N = \mathbf v_{\rm ring}+\nabla\psi,
\]

where `v_ring` carries the circulation and a single-layer BEM potential `psi` corrects the torus boundary condition

\[
\mathbf n\cdot\mathbf v_N\approx 0
\quad\text{on}\quad
\partial\mathcal T_\lambda.
\]

## What this version regenerates

It regenerates all important previous calculations and adds the three numerical audits requested in the discussion:

1. **Ring-only reference**: shows the near-\(2\pi\) kinetic value can occur while Neumann fails.
2. **BEM-corrected reference**: boundary-corrected Neumann candidate at one \(\lambda\).
3. **Lambda sweep**: \(\lambda=1.05,1.10,1.20,1.50,2.00\) by default.
4. **Panel-refinement audit**: e.g. `8x16 -> 12x24 -> 16x32` BEM panels.
5. **Volume-refinement audit**: e.g. `n_volume=14 -> 18 -> 22`.
6. **One-sided offset-boundary probe**: evaluates `x + eps*n` for eps = `1e-1,1e-2,1e-3,1e-4` to separate BEM jump-operator residual from direct surface-probe noise.
7. **Audit summary**: a compact machine-readable verdict.

## Package contents

```text
sst_horn_bem/
  __init__.py
  core.py                    Public API and backend dispatch
  fallback.py                NumPy dense-BEM backend and offset probe
  audits.py                  Panel/volume/offset/regeneration audits
  build_ext_if_needed.py     pybind11 change-detecting build script with Windows link fix
cpp/
  horn_bem.cpp               Dense pybind11 BEM backend
run_horn_bem.py              One-shot run
run_horn_sweep.py            Lambda sweep
run_panel_refinement.py      Audit 1: BEM panel refinement
run_volume_refinement.py     Audit 2: volume integration refinement
run_offset_probe.py          Audit 3: one-sided offset-boundary probe
run_all_audits.py            Regenerate all key previous and new calculations
examples/minimal_commands.txt
```

## Build

The package works without compilation through NumPy fallback.  With pybind11 and a C++17 compiler:

```bash
python -m sst_horn_bem.build_ext_if_needed --force
```

Strict CI build:

```bash
python -m sst_horn_bem.build_ext_if_needed --force --strict
```

The build script hashes `cpp/horn_bem.cpp` and only rebuilds when it changes.  On Windows/MinGW it adds Python import-library link flags, e.g. `-L.../libs -lpython314`.

## Minimal commands

```bash
# Ring-only reference
python run_horn_bem.py --lambda 1.2 --no-bem --out horn_ring_1p2_no_BEM.json

# BEM-corrected reference
python run_horn_bem.py --lambda 1.2 --bem --bem-n-eta 12 --bem-n-phi 24 --out horn_bem_1p2.json

# Lambda sweep
python run_horn_sweep.py --lambdas 1.05,1.1,1.2,1.5,2.0 --bem --out-json horn_bem_sweep.json --out-csv horn_bem_sweep.csv

# Three new audits
python run_panel_refinement.py --lambda 1.2 --panel-grids 8x16,12x24,16x32
python run_volume_refinement.py --lambda 1.2 --n-volumes 14,18,22
python run_offset_probe.py --lambda 1.2

# Everything into one output folder
python run_all_audits.py --out-dir audit_out

python run_all_audits.py  --lambda 1.2  --lambdas 1.05,1.1,1.2,1.5,2.0  --panel-grids 8x16,12x24,16x32,24x48  --n-volumes 14,18,22,26  --n-ring 256  --n-surface 32  --bem-n-eta 12  --bem-n-phi 24  --box-radius 6.0  --out-dir audit_out_full
```

Use `--force-python` on any script to bypass pybind11 and force the NumPy backend.

## Result interpretation guard

The primary BEM Neumann gate is the boundary-operator residual.  A direct surface probe omits the single-layer jump term and is therefore reported separately as diagnostic noise:

```text
neumann_boundary_error                 primary BEM operator gate
neumann_boundary_error_direct_probe    noisy direct surface probe
offset_probe                           one-sided x+eps*n exterior probe
```

A BEM run is numerically useful only when the following are jointly stable under refinement:

\[
\epsilon_N,\quad
\Delta\Gamma_{\rm BEM},\quad
\chi_K(h),\quad
\chi_K(n_{\eta},n_{\phi}),\quad
\chi_K(n_{\rm volume}),\quad
\epsilon\to0^+\text{ offset probe}.
\]

## Hard analytic guard

If cavitation work counts positively in inertial rest energy, the hollow horn-torus cannot realize \(\chi_E=2\pi\), because

\[
\chi_E^{\rm hollow,horn}=\chi_K^{\rm horn}+\pi^2>2\pi.
\]

Therefore the package always reports kinetic-only, cavitation, and hollow total-energy factors separately.

## Status labels

- **Research Track / Frozen Audit Problem**: decomposition and numerical gates.
- **Not Canon / Derived Mass Coefficient**: no claim that \(\chi_E=2\pi\) is derived.
- **Route-K target**: exterior Neumann Dirichlet-energy benchmark.
- **Route-B inspiration only**: BEM/audit style, not Steklov/zeta spectral action.