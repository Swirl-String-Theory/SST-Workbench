# 2_Maxwell_SST_Dynamical_Field_Closure_Falsifier_v0.2.0

Windows-first workbench for chat/workbench prefix **2_**.

Intended location:

```text
C:\workspace\projects\SST-Workbench\SST_Maxwell\2_Maxwell_SST_Dynamical_Field_Closure_Falsifier_v0.2.0
```

Default relaxed-knot input:

```text
C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

## What v0.2.0 adds

- keeps the v0.1.0 blind **DFC-T / DFC-D / DFC-G** gates;
- adds direct intake of the relaxed `*_final.txt` KnotPlot/RidgeRunner centerlines;
- compares recomputed centerline length against companion `.metrics.json` where available;
- adds C++17/pybind11 native kernels based on the supplied `SST_cpp_pybind_audit_template` pattern: build-if-needed, Python fallback, and native/Python parity checks;
- adds a multithreaded Neumann-like centerline interaction kernel, its analytic translation-gradient force, and a finite-core Biot-Savart kernel;
- adds BASIC and EXTENDED Windows campaigns with timestamped output directories;
- preserves scientific separation between **geometry/reduced-kernel diagnostics** and the full blind DFC gates.

## Important interpretation guard

The relaxed knot centerlines by themselves are **not enough** to pass DFC-T or DFC-D: those require unreduced dynamical mode data and independently reconstructed polarization/current/charge channels. The reduced pair scan is also **not accepted as DFC-G evidence**, because its force is an analytic gradient channel of the same reduced kernel, not an independent SST surface-stress/momentum-flux reconstruction.

This is deliberate: v0.2.0 accelerates and audits the geometry layer without manufacturing a false physics closure.

## One-click Windows workflow

Run in this order:

```text
run_00_install.cmd
run_01_basic.cmd
run_02_extended.cmd
```

Or use:

```text
run_99_all.cmd
```

`run_00_install.cmd` creates `.venv`, installs NumPy/pytest/pybind11/build tooling, builds the C++ extension, and runs a native smoke test.

`run_01_basic.cmd` runs synthetic blind positive/negative controls plus three representative relaxed geometries (`knot_3.1`, `knot_4.1`, `torus_2.3`) and native/Python parity.

`run_02_extended.cmd` processes every `*_final.txt` in the default knot directory, on x/y/z separation axes, with a larger resampled centerline and reduced pair scans.

## Full blind solver data

When real solver outputs exist, place the three files described in `schemas/DATA_CONTRACT.md` in a campaign directory and run:

```text
run_03_blind_campaign.cmd C:\path\to\campaign
```

After the frozen result is archived:

```text
run_04_reveal.cmd C:\path\to\campaign\frozen_result.json
```

## C++ backend

The native extension is compiled with `/O2 /std:c++17` under MSVC or `-O3 -std=c++17` elsewhere. The hot pairwise kernels release the Python GIL and use `std::thread`; `SST_NATIVE_THREADS` defaults to `%NUMBER_OF_PROCESSORS%` in the CMD wrappers.

If MSVC is unavailable, Python fallback exists for correctness, but `run_02_extended.cmd` uses `--require-native` by default because the all-knot pair scan is intentionally C++ accelerated.

## Exit codes

```text
0 = PASS / completed
2 = FAIL (a preregistered or geometry/parity check failed)
3 = INVALID (blind DFC campaign violates input/independence declarations)
```
