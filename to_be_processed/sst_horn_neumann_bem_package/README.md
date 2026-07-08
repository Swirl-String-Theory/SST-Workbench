# SST Horn-Torus Neumann BEM Audit Package

Research-track / frozen-audit package for the horn-torus exterior Neumann Dirichlet-energy problem.

This is **not** a canon proof of \(\chi_E=2\pi\). It is a numerical falsification/validation harness that separates:

\[
\chi_K(\lambda)=\frac12\int_{\Omega_\lambda}|\nabla\phi_\lambda|^2\,d^3\xi,
\qquad
\chi_{\rm cav}(\lambda)=\pi^2\lambda,
\qquad
\chi_E^{\rm hollow}=\chi_K+\chi_{\rm cav}.
\]

The package implements the concrete Neumann plan:

\[
\mathbf v_N = \mathbf v_{\rm ring} + \nabla\psi,
\]

where `v_ring` carries the circulation and the single-valued single-layer potential `psi` corrects the torus boundary so that

\[
\mathbf n\cdot\mathbf v_N\approx0
\quad\text{on}\quad\partial\mathcal T_\lambda.
\]

## Contents

```text
sst_horn_bem/
  __init__.py
  core.py                    Python public API
  fallback.py                NumPy dense-BEM fallback backend
  build_ext_if_needed.py     pybind11 change-detecting build script
cpp/
  horn_bem.cpp               C++ dense BEM backend
run_horn_bem.py              one-shot CLI
run_horn_sweep.py            lambda sweep CLI
examples/
  minimal_commands.txt
```

## Install/run

From this directory:

```bash
python -m sst_horn_bem.build_ext_if_needed --force
python run_horn_bem.py --lambda 1.2 --bem --bem-n-eta 12 --bem-n-phi 24 --n-volume 18 --out run1
python run_horn_sweep.py --lambdas 1.05,1.1,1.2,1.5,2.0 --bem --bem-n-eta 12 --bem-n-phi 24  --out-json sweep run_sweep
```

```bash
python run_horn_bem.py --lambda 1.2 --bem --bem-n-eta 12 --bem-n-phi 24 --n-ring 256 --n-surface 32 --n-volume 18 --box-radius 6.0 --out horn_bem_1p2.json

# Compare against the uncorrected ring field.
python run_horn_bem.py --lambda 1.2 --no-bem --n-ring 256 --n-surface 32 --n-volume 18 --box-radius 6.0 --out horn_ring_1p2.json

# Sweep.
python run_horn_sweep.py --lambdas 1.05,1.1,1.2,1.5,2.0 --bem --bem-n-eta 12 --bem-n-phi 24 --out-json horn_bem_sweep.json --out-csv horn_bem_sweep.csv

```

If `pybind11` or a compatible C++ compiler is missing, the code falls back to the NumPy backend. Use `--force-python` to force that path.

## CI / strict build

```bash
python -m sst_horn_bem.build_ext_if_needed --force --strict
```

## Main diagnostics

The result dictionary reports:

- `chi_K`: kinetic Dirichlet factor from the corrected field.
- `chi_cav`: analytic cavitation factor \(\pi^2\lambda\).
- `chi_E_hollow`: `chi_K + chi_cav`.
- `neumann_boundary_error`: independent surface residual for \(n\cdot v=0\).
- `bem_predicted_neumann_error`: residual on the BEM panel grid.
- `circulation_signed`, `circulation_magnitude_error`, `circulation_signed_error`.
- `bem_correction_circulation`: should remain approximately zero.
- `divergence_error`, `curl_error`, `farfield_decay_error`.
- gate booleans for first acceptance and strict thresholds.

## Interpretation guard

Even if \(\chi_K\) approaches \(2\pi\), the hollow-core total-energy benchmark cannot equal \(2\pi\) if cavitation work counts positively:

\[
\chi_E^{\rm hollow,horn}=\chi_K^{\rm horn}+\pi^2>2\pi.
\]

Therefore this package keeps kinetic-only, cavitation, and total hollow-core factors separate.

## Route-B inspiration, Route-K target

This package borrows the Route-B idea of auditable BEM kernels, mesh sweeps, and convergence certificates, but it is **not** a Steklov/zeta spectral-action solver. The target here is Route-K:

\[
\text{exterior Neumann harmonic field}\rightarrow\chi_K(\lambda)\rightarrow\lambda\to1^+.
\]