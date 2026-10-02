# SST Dark-Knot Rayleigh / Rocking Harness

Research-Track audit package generated from `SST_cpp_pybind_audit_template`.

This folder keeps the template pattern:

- `cpp/` — optional pybind11 kernels for quadrupole and regularized Biot-Savart velocity.
- `sst_dark_knot_harness/` — Python package with C++ loader, fallback, core diagnostics.
- `run_example.py` — single diagnostic run.
- `run_sweep.py` — sweep over `epsilon_BS` and `Omega`.
- `run_all_checks.py` — smoke + sweep battery.
- `examples/` — copy-paste commands.

## Status

This is **Research Track**, not canonical physics. It implements the diagnostic split

\[
\Phi_{\rm R}(r;K)=4\Omega^2+2\Omega A_K+B_K,
\]

with

\[
\Delta_\Omega(K)=\langle\Phi_{\rm R}(+\Omega;K)-\Phi_{\rm R}(-\Omega;K)\rangle
=4\Omega\langle A_K\rangle,
\]

and

\[
\widehat\Sigma_\Omega(K)=
\frac{\langle\Phi_{\rm R}(+\Omega;K)+\Phi_{\rm R}(-\Omega;K)-8\Omega^2\rangle}{8\Omega^2}
=\frac{\langle B_K\rangle}{4\Omega^2}.
\]

Canon-safe interpretation:

\[
4_1 \text{ is tested as first-order chirality-blind, not dynamically inert.}
\]

## Baseline parameters

The default nondimensional ropelength setup uses

\[
\tau=1,\qquad \epsilon_{\rm BS}=1,\qquad h=0.5,\qquad \Delta r=0.25.
\]

Generated default centerlines are scaled to the reference ropelength targets:

- `3_1`: `32.7436`
- `4_1`: `42.0887`

These are used only for the default synthetic input geometry. For final results, supply Ridgerunner-relaxed CSV centerlines.

## Quick start

```bash
cd SST_dark_knot_rayleigh_harness

# Optional C++ build; Python fallback remains usable.
python -m sst_dark_knot_harness.build_ext_if_needed --force

# Diagnostic run for 4_1. Rocking/breathing unavailable unless response vertices are supplied.
python run_example.py --knot 4_1 --n 256 --omega 1.0 --epsilon-bs 1.0 --summary-only

# Smoke-only synthetic response for checking the rocking/breathing output fields.
python run_example.py --knot 4_1 --n 256 --proxy-response-gain 0.02 --summary-only

# Sensitivity sweep.
python run_sweep.py --knots 3_1,4_1 --omegas 0.5,1.0 --epsilons 0.5,1.0,2.0 --out-json sweep.json --out-csv sweep.csv

# Full check battery.
python run_all_checks.py --out-dir audit_out
```


```bash
python ideal_favorites_to_csv.py ideal_favorites.txt --id 4:1:1 --n 512 --center --scale-to-declared-L --out V0_4_1.csv

# Voor trefoil:

python ideal_favorites_to_csv.py ideal_favorites.txt --id 3:1:1 --n 512 --center --scale-to-declared-L --out V0_3_1.csv

# Daarna kun je je harness draaien met:

python run_example.py --knot 4_1 --input-csv V0_4_1.csv --omega 1.0 --epsilon-bs 1.0 --out audit_4_1_base.json

# Of voor trefoil:

python run_example.py --knot 3_1 --input-csv V0_3_1.csv --omega 1.0 --epsilon-bs 1.0 --out audit_3_1_base.json

python make_response_pair_proxy.py V0_4_1.csv  --knot 4_1  --omega 1.0  --gain 0.02  --n 512  --out-plus Vplus_4_1.csv  --out-minus Vminus_4_1.csv  --report response_pair_proxy_report.json

python make_response_pair_proxy.py V0_3_1.csv  --knot 3_1  --omega 1.0  --gain 0.02  --n 512  --out-plus Vplus_3_1.csv  --out-minus Vminus_3_1.csv  --report response_pair_proxy_report.json
```


# Full command examples — run from the package root.

```bash

# Build C++ backend if pybind11 and compiler are available.
python -m sst_dark_knot_harness.build_ext_if_needed
python -m sst_dark_knot_harness.build_ext_if_needed --force
python -m sst_dark_knot_harness.build_ext_if_needed --force --strict

# Single 4_1 Rayleigh audit.
python run_example.py --knot 4_1 --n 256 --omega 1.0 --epsilon-bs 1.0 --shell-dr 0.25 --shell-h 0.5 --summary-only

# Single 3_1 control audit.
python run_example.py --knot 3_1 --n 256 --omega 1.0 --epsilon-bs 1.0 --summary-only

# Force Python fallback only.
python run_example.py --knot 4_1 --force-python --summary-only

# Smoke-only synthetic rocking/breathing response.
python run_example.py --knot 4_1 --proxy-response-gain 0.02 --out smoke_proxy_4_1.json

# Use actual relaxed response vertices.
python run_example.py --knot 4_1 --input-csv V0_4_1.csv --vertices-plus Vplus_4_1.csv --vertices-minus Vminus_4_1.csv --out audit_4_1_real_response.json

python run_example.py --knot 3_1 --input-csv V0_3_1.csv --vertices-plus Vplus_3_1.csv --vertices-minus Vminus_3_1.csv --out audit_3_1_real_response.json

# Regularization sweep.
python run_sweep.py --knots 3_1,4_1 --omegas 0.25,0.5,1.0 --epsilons 0.5,1.0,2.0 --n 256 --out-json sweep.json --out-csv sweep.csv

# Full battery.
python run_all_checks.py --out-dir audit_out
python run_all_checks.py --out-dir audit_out_python --force-python
```

## CSV input format

Base and response vertices use CSV with either a header

```csv
x,y,z
0.0,1.0,0.0
...
```

or three headerless numeric columns.

Use actual solver outputs like this:

```bash
python run_example.py \
  --knot 4_1 \
  --input-csv V0_4_1.csv \
  --vertices-plus Vplus_4_1.csv \
  --vertices-minus Vminus_4_1.csv \
  --omega 1.0 \
  --epsilon-bs 1.0 \
  --out audit_4_1.json
```

## Important limitation

`active_constraint_summary()` currently logs a vertex-vertex strut proxy and MinRad/kink proxy. It does **not** replace the full Ridgerunner `dcsd + MinRad± + NNLS` projection. The package is designed to ingest real Ridgerunner output first; full `Pi_I(V)` evolution should be wired in after the regularization audit is stable.

## Files to edit next

| File | Purpose |
|---|---|
| `sst_dark_knot_harness/core.py` | Main diagnostics and sweep logic. |
| `cpp/native.cpp` | Optional C++ acceleration kernels. |
| `run_example.py` | CLI for one audit. |
| `run_sweep.py` | CLI for regularization sensitivity scans. |
| `PROJECTED_GRADIENT_NOTES.md` | Roadmap for full `Pi_I(V)` integration. |
## v1.1 audit-source semantics

The harness now records input provenance in a top-level `source` block. This prevents a proxy or manually edited `Vplus/Vminus` pair from being mistaken for a physical projected Ridgerunner relaxation.

`--response-source auto` is the default. It infers proxy when `--proxy-response-gain` is used, detects a matching `response_pair_proxy_report.json` where possible, and otherwise labels supplied `Vplus/Vminus` files as `external_csv_unverified`.

Use `--response-source projected_ridgerunner`, `--response-source ridgerunner`, or `--response-source solver` only when the supplied response vertices came from a real constrained relaxation with thickness/contact checks. In all other cases, `rocking_breathing` is treated as pipeline validation rather than physical evidence.
