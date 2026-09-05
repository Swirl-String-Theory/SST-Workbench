# 1_Maxwell_SST_Kinetic_Falsifier v0.2.0

Workbench **#1** for the SST research track **“Maxwell–SST Kinetic Closure and Internal-Mode Thermodynamic Gate.”**

This release keeps the strict v0.1 falsifier and adds a solver-facing centerline workflow aimed at the question:

> For each SST knot `K`, which translation, orientation, Kelvin/shape, twist, writhe and core degrees of freedom are actually coupled by an interaction, what are their gaps, and what thermodynamic/spectroscopic contribution follows?

## What v0.2.0 adds

- KnotPlot/Geomview `VECT` importer plus XYZ/CSV/NPY import.
- Uniform arclength resampling.
- Geometry audit: length, segment uniformity, curvature, RMS radius and midpoint-Gauss writhe diagnostic.
- Explicit removal of rigid translation and global rotation directions.
- A rigid-projected normal Fourier deformation basis as **Kelvin/shape candidates**.
- A regularized centerline Biot–Savart encounter probe.
- Decomposition of interaction response into translation, rotation and residual shape response.
- Projection of residual shape response onto the Kelvin/shape candidate basis.
- Directional writhe response and minimum inter-filament distance.
- C++17/pybind11 acceleration based on the supplied `SST_cpp_pybind_audit_template`: hash-based rebuild, native-first dispatch, Python fallback.
- Automatic creation of a v0.1-compatible physical campaign skeleton for later energy/gap/thermodynamic data.

## Critical interpretation boundary

v0.2.0 does **not** invent the missing SST energy functional. Therefore:

- `mode_candidates.csv` contains geometry deformation candidates, **not a derived physical eigenspectrum**;
- `interaction_coupling_proxy.csv` contains regularized Biot–Savart geometric response, **not mode energy transfer**;
- no `gap_eV` is inferred from a positive frequency or from the proxy;
- twist remains unavailable without a resolved material frame;
- core modes remain unavailable without a resolved finite-core field;
- thermodynamics/spectroscopy remain in the strict v0.1 physical falsifier and require physical solver or experimental inputs.

That separation is deliberate: a centerline-only solver cannot honestly manufacture twist/core gaps.

## Expected Windows location

```text
C:\workspace\projects\SST-Workbench\SST_Maxwell\1_Maxwell_SST_Kinetic_Falsifier_v0.2.0
```

Default knot directory already configured in `config\paths.cmd`:

```text
C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

The scripts prefer the shared SST Workbench environment:

```text
C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe
```

## Ready-made commands

Run in this order:

```cmd
run_00_install.cmd
run_01_check_backend.cmd
run_10_basic.cmd
run_20_extended.cmd
```

Or:

```cmd
run_all_basic.cmd
```

and later:

```cmd
run_all_extended.cmd
```

### What they do

| Script | Purpose |
|---|---|
| `run_00_install.cmd` | Installs package/tests, attempts pybind11 C++ build, runs unit tests. |
| `run_01_check_backend.cmd` | Prints active backend and runs a synthetic VECT smoke workflow. |
| `run_10_basic.cmd` | All discovered final knots, 300-point resampling, `m<=6`, one self-copy encounter per curve. C++ preferred, Python fallback allowed. |
| `run_20_extended.cmd` | 1200-point resampling, `m<=16`, 16 self-copy encounter configurations per curve. **C++ required.** |
| `run_21_extended_unique_pairs.cmd` | Same resolution but all unique curve pairs. Potentially expensive. |
| `run_30_physical_falsifier.cmd` | Runs the strict thermodynamic/spectroscopic falsifier after physical CSV data have been populated. |
| `run_90_tests.cmd` | Unit tests. |

`run_basic.cmd`, `run_extended.cmd`, and `run_install.cmd` are short aliases.

## Basic output

`outputs\basic\` contains:

```text
discovered_files.csv
geometry_metrics.csv
mode_candidates.csv
interaction_coupling_proxy.csv
workflow_summary.json
README_RESULTS.md
resampled_unit_rms\*.csv
v01_physical_campaign_skeleton\
```

The `v01_physical_campaign_skeleton` is intentionally incomplete. Fill it only from a declared physical SST solver/experiment before calling `run_30_physical_falsifier.cmd`.

## C++ acceleration

The native kernel is in:

```text
cpp\native.cpp
```

It accelerates the expensive `O(N^2)` operations:

- regularized Biot–Savart velocity;
- midpoint writhe diagnostic;
- inter-segment minimum distance;
- segment lengths.

The pybind loader follows the supplied SST template philosophy:

1. hash the C++ source;
2. rebuild only when needed;
3. use C++ when import succeeds;
4. retain a mathematically equivalent NumPy/Python fallback.

On Windows, the builder first uses `setuptools build_ext`, which is the most reliable route to MSVC Build Tools. If the C++ build is unavailable, basic work still runs; extended intentionally refuses to silently fall back because an `N=1200` multi-encounter campaign is unnecessarily slow in pure Python.

## Direct CLI

```cmd
python -m maxwell_sst_falsifier backend --force-build

python -m maxwell_sst_falsifier workflow ^
  --knots-dir "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final" ^
  --out "outputs\basic" ^
  --preset basic ^
  --threads 16
```

Strict physical falsifier:

```cmd
run_30_physical_falsifier.cmd ^
  outputs\extended\v01_physical_campaign_skeleton\config.json ^
  outputs\physical_audit
```

Do that last command only after the physical CSV tables have been populated; blank placeholders are not physical evidence.

See `docs\RUNBOOK.md` and `docs\CXX_BACKEND.md` for details.
