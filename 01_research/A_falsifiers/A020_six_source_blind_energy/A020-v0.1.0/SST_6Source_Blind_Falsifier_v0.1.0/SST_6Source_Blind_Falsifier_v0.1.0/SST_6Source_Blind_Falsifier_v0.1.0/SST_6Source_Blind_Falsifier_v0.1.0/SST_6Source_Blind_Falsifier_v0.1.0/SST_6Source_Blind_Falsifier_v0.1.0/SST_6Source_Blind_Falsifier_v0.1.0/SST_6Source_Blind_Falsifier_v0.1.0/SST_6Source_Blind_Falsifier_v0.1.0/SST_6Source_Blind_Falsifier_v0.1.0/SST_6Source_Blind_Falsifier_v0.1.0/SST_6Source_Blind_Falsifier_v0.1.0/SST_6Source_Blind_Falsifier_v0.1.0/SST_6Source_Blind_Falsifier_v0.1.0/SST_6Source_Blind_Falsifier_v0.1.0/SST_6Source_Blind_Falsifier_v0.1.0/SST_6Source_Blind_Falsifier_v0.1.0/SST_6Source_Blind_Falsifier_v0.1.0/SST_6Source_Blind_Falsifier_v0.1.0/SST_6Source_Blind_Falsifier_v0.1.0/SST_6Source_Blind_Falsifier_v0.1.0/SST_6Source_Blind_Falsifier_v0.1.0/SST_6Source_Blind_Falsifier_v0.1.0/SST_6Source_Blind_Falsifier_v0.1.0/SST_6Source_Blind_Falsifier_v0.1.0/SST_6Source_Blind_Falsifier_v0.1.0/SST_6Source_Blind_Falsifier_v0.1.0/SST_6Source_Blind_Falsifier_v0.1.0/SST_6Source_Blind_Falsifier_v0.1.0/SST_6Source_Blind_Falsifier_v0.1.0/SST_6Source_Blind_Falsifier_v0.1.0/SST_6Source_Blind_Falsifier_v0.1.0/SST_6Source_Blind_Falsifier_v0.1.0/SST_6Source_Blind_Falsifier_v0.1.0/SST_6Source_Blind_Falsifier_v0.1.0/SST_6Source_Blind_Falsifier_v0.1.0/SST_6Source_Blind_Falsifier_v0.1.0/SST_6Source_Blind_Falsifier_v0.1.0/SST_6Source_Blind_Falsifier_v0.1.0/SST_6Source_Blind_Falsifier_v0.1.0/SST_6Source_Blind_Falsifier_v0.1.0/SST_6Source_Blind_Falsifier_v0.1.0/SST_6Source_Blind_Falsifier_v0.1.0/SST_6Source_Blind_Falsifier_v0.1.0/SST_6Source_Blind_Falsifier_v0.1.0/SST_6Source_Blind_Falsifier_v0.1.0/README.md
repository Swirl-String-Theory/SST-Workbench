# SST Six-Source Blind Falsifier v0.1.0

A large, preregistered falsifier package built from the supplied `SST_cpp_pybind_audit_template.zip` and the six-source analysis sequence:

1. Uosukainen — turbulence as sound source / transport stress and multipoles
2. Abe & Okuyama — modal additivity, phase erasure, thermodynamic closure guards
3. Rossby — gradient-selected scale / potential-vorticity analogy guard
4. Kleckner, Kauffman & Irvine — knot perturbations, contacts, reconnection precursors
5. Zheng et al. — Hopfion scale selection, framed topology, formation/stability discipline
6. Helmholtz — resonator null model, phase/amplitude closure, nonlinear-mixing controls

The package is deliberately **blind by default**. It does not read particle masses, desired SST output values, or topology-to-particle assignments. Dataset subsampling and perturbation seeds are derived from file-content hashes and preregistered gate IDs.

## Quick start on Windows

From this folder:

```cmd
run_all.cmd
```

Default dataset search order:

```text
..\..\KnotPlot\knots\final
..\KnotPlot\knots\final
KnotPlot\knots\final
data\sample_knots
```

Or pass the dataset explicitly:

```cmd
run_all.cmd C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

`run_all.cmd` performs the complete chain:

```text
create .venv
  -> pip install dependencies
  -> build C++17 pybind11 extension
  -> preflight
  -> C++/Python parity audit
  -> BASIC blind campaign
  -> EXTENDED blind campaign
  -> combined RUN_ALL_SUMMARY.json
```

The full run intentionally requires the native extension. If MSVC/C++ is unavailable, use:

```cmd
run_fallback_sample.cmd
```

for a small Python-only smoke test.

## Other ready-to-run CMD files

```cmd
run_install.cmd
run_native_audit.cmd
run_basic.cmd [dataset]
run_extended.cmd [dataset]
run_all.cmd [dataset]
run_fallback_sample.cmd
```

## Output layout

A full run creates:

```text
outputs\run_all_YYYYMMDD_HHMMSS\
├── RUN_ALL_SUMMARY.json
├── basic\
│   ├── 00_preregistration_manifest.json
│   ├── 01_runtime.json
│   ├── all_results.json
│   ├── all_results_flat.csv
│   ├── SUMMARY.json
│   ├── selection_*.json
│   └── items\<item>\<gate>.json
└── extended\
    └── ... same structure ...
```

A physical/model `FAIL` is **not a runtime error**. Falsification is a valid scientific result. The process exits non-zero only for build failures, calibration failures, numerical-identity failures, or exceptions.

## Native kernels

The C++ extension accelerates:

- regularized Biot–Savart velocity evaluation;
- finite-core double-integral self-induction energy;
- Gauss linking integral;
- Gauss writhe integral;
- nonlocal segment-contact search with exact segment/segment distance.

A pure NumPy/Python fallback is included for auditability, but the EXTENDED campaign is intended for C++.

## Core normalization

Relaxed KnotPlot/Ridgerunner files are treated as dimensionless geometry. When a matching `*.metrics.json` exists, `thickness` is used as the baseline resolved core radius. Geometry gates operate primarily in **core units**:

```text
a_core = 1
Gamma  = 2*pi
rho    = 1
```

This prevents huge/small SI numbers from affecting numerical conditioning. The canonical SI constants are recorded in every preregistration manifest:

```text
v_swirl = 1.09384563e6 m s^-1
r_c     = 1.40897017e-15 m
rho_f   = 7.0e-7 kg m^-3
Gamma_0 = 9.68361920e-9 m^2 s^-1
```

The H5 scale gate additionally reports the baseline self-induction energy in SI using these canonical values, but **does not fit it to any particle mass**.

## Verdict tiers

- `CALIBRATION` — validates the analysis machinery, not SST physics.
- `PRIMARY_*IDENTITY` — numerical/geometric identities that should pass if implementation and resolution are sound.
- `PRIMARY_STATIC_FIELD` — direct static-field consequence of the declared regularized incompressible model.
- `PRIMARY_RESEARCH_HYPOTHESIS` — a genuine falsifiable SST research closure.
- `MODEL_CONDITIONAL` — tests a declared reduced model; failure rejects that reduction, not SST globally.
- `DIAGNOSTIC` — reports a physically relevant condition but does not produce a project pass/fail.
- `PROXY_DIAGNOSTIC` — source-inspired analogy deliberately excluded from the primary verdict.

See `docs/GATE_MATRIX.md` for the exact interpretation of each gate.

## Blind protocol

The campaign manifest is written **before** gate evaluation. It stores:

- all input SHA-256 hashes;
- configuration and configuration hash;
- canonical SST constants;
- gate thresholds;
- blind dataset-selection hash;
- explicit declaration that no empirical particle-mass targets were used.

Subset selection is based on:

```text
SHA256(config + sorted input file hashes + gate_id)
```

and random perturbations use:

```text
SHA256(file content hash + gate_id)
```

so filenames and particle labels do not determine which samples are chosen.

## Important scientific boundary

The package does **not** silently equate:

- GP reconnection with ideal incompressible Euler reconnection;
- Rossby potential vorticity with a universal 3-D knot invariant;
- curvature-spectrum power with thermodynamic probability;
- a framed-curve self-linking number with a field-space Hopf invariant;
- an acoustic Helmholtz resonance with an SST torsional/R-phase mode.

Those are kept as conditional or proxy gates where appropriate.

## Sample data

`data/sample_knots/` contains three real relaxed files from the supplied relaxed-knot archive so installation and parsing can be tested without an external directory. The production run should point to the complete `KnotPlot\knots\final` dataset.

## Version

`v0.1.0` is the first integrated six-source falsifier. It is intentionally a **workbench precursor**, not a Canon patch. The next logical step is to use its outcomes to decide which gates deserve dedicated research tracks and full dynamical solvers.
