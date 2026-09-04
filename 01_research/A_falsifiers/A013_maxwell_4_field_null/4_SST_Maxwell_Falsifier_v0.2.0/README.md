# 4_SST Maxwell Falsifier Workbench v0.2.0

Workbench prefix: **`4_`**. This is the v0.2.0 continuation of the seven-test Maxwell falsifier.

## What changed from v0.1.0

- All deliverable/package/output names are namespaced with the **4_** workbench prefix.
- Default KnotPlot source is exactly `..\..\KnotPlot\knots\final` relative to this workbench.
- Batch discovery reads every `*_final.txt`/VECT/NPY/NPZ file in that directory.
- Companion `*.metrics.json` is used to split concatenated multi-component links correctly via `vertices_per_component`.
- T02 and T04 are now multi-component aware; T02 reports the pairwise Gauss-linking matrix and tests each component meridian against the total velocity field.
- T07 evaluates the combined compact field of all components and remains a deliberate Newtonian-tail negative control.
- T05 runs a component-local energy/helicity stationarity diagnostic for links; mutual-interaction stationarity is **not** silently claimed.
- The supplied `SST_cpp_pybind_audit_template` auto-build pattern is integrated as `native_ext/`.
- C++17/pybind11 kernels accelerate Biot--Savart, Gauss linking, regularized energy, and writhe. OpenMP is attempted first; optimized serial C++ is the fallback; NumPy/Python is the final fallback.

## Ready-to-run Windows commands

From the unpacked workbench directory (both the plain `run_*` names and `4_run_*` aliases are included):

```bat
run_install.cmd
run_native_preflight.cmd
run_basic.cmd
run_extended.cmd
```

Or everything sequentially:

```bat
run_all.cmd
```

The scripts default to:

```text
..\..\KnotPlot\knots\final
```

You can override that directory:

```bat
run_basic.cmd C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
run_extended.cmd C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

Default native thread count is 16. Override it before running:

```bat
set SST_NATIVE_THREADS=12
run_extended.cmd
```

## Presets

**Basic**: all discovered final geometries at `N=240` per component, fast T02/T04/T05/T07 plus the synthetic T01/T03/T06 controls.

**Extended**: all discovered geometries at `N=300,600,1200` per component. T02/T04/T07 run at every level; expensive T05 stationarity runs at `N=600`. This is a numerical quadrature/convergence ladder, not a claim that interpolation creates new geometric resolution.

## One geometry

```bat
run_one.cmd ..\..\KnotPlot\knots\final\knot_3.1_final.txt 600
```

## Seven Maxwell-inspired falsifiers

T01 material swirl-tonic/Stokes; T02 circulation/topological holonomy; T03 moving-loop identity; T04 exterior Hodge/harmonic sector; T05 energy--helicity stationarity; T06 cyclic-work/chirality response; T07 derived radial force-flux negative control.

The inadmissible direct route **"Maxwell 1/r pressure -> SST gravity" remains excluded**.

## Native backend

`run_install.cmd` creates a local `.venv`, installs Python requirements, installs this workbench editable, and attempts the C++ build. The local environment is deliberate: it prevents the five parallel Maxwell workbenches from overwriting one another's editable Python package/backend. `run_native_preflight.cmd` is strict: it returns a nonzero exit code if the native extension cannot be built.

On Windows, install Visual Studio 2022 Build Tools with **Desktop development with C++** if native compilation is unavailable.

## Outputs

Each run writes a timestamped `4_outputs_basic_*` or `4_outputs_extended_*` directory containing:

- `summary.json`
- `summary.csv`
- `synthetic.json`
- one JSON record per knot/link/torus geometry
- native backend and timing metadata

Geometry sidecars are copied into the report logically (residual, ropelength, thickness, component count, vertex counts, edge CV/ratio) without silently upgrading their certification status.

## Canon patch

The v0.1.0 Canon patch is preserved under `CANON_PATCH/` with a `4_` filename prefix. v0.2.0 changes the computational workbench; it does not silently change the Canon semantics.
