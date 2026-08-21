# v0.1.2 dataset resolver hotfix

v0.1.2 fixes the post-native-build failure where an existing but empty/wrong
KnotPlot directory was accepted and the blind prepare stage then failed with
`no files matching *_i10000.txt`.

The resolver is now **content based**:

1. an explicit input path is accepted only if it really contains `*_i10000.txt`;
2. the normal one/two-level sibling layouts are searched;
3. both campaign workspace spellings `solo_projects` and `solo\\_projects` are checked when present;
4. legacy nested source layout `KnotPlot\\_3p1\\_MultiDynamics\\_Relaxation\\_Matrix\\_v0.1.0` is included;
5. nearby KnotPlot roots are scanned for the actual final-checkpoint files;
6. ties fail explicitly rather than silently choosing a dataset;
7. if only earlier checkpoints exist, their counts are printed and the run stops.

The preregistered blind test still requires the **same `i10000` checkpoint** for all
candidates. It does not silently substitute `i04000` or `i01000`.

Before a full run you can now execute:

```bat
run_05_find_input.cmd
```

or pass a dataset explicitly:

```bat
run_05_find_input.cmd "C:\\path\\to\\matrix-output"
run_all.cmd "C:\\path\\to\\matrix-output" basic
```

---


## v0.1.2 Windows/MSVC + input-path hotfix

The target workstation log showed that dependency installation completed and the native build reached `build_ext`, but setuptools failed before `cl.exe` was spawned because its nested `cmd /u /c vcvarsall.bat ... && set` returned a non-zero status. v0.1.2 initializes/reuses MSVC in the parent CMD process and sets `DISTUTILS_USE_SDK=1`, so setuptools no longer launches a second `vcvarsall.bat`. The actual native gate is now `where cl.exe`, `where link.exe`, import of the compiled backend, and Python/C++ parity.

The default KnotPlot matrix path is also resolved robustly from either one or two parent levels. This matches the common layout where the falsifier sits inside an SST subfolder while `KnotPlot` is a sibling at the SST-Workbench root.

If the user's CMD AutoRun itself emits `The system cannot find the path specified`, that warning is external to this package. Running from an IDE may still print it once, but v0.1.2 prevents setuptools from triggering the same AutoRun/`vcvarsall` path again during compilation.

# SST Phase Feedback Delay Knot Stability Blind Falsifier v0.1.2

C++17/pybind11 + Python blind falsifier for the question:

> Does a finite self-return phase delay predict which relaxed vortex-knot geometries are dynamically more stable?

It follows the established SST workbench pattern: native C++ kernel, Python orchestration/fallback, strict native preflight, staged `.cmd` scripts, sealed blind IDs, frozen evaluation, then reveal. The architecture is aligned with the prior SST Kelvin/Floquet C++/pybind workbench pattern. 

## Designed input

By default the Windows scripts look for the current KnotPlot relaxation matrix at:

```text
..\KnotPlot\KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0
```

and ingest only terminal checkpoints:

```text
*_i10000.txt
```

You can override the input directory:

```bat
run_all.cmd "C:\workspace\solo\_projects\SST-Workbench\KnotPlot\KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0"
```

## Recommended scientific workflow

First freeze the blind result without revealing preparation labels:

```bat
run_all_blind.cmd "C:\workspace\solo\_projects\SST-Workbench\KnotPlot\KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0" basic
```

Inspect:

```text
results\BLIND_EVALUATION.json
results\BLIND_EVALUATION.sha256.txt
```

Then reveal:

```bat
run_40_reveal.cmd
```

Or use the one-command convenience workflow:

```bat
run_all.cmd "C:\workspace\solo\_projects\SST-Workbench\KnotPlot\KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0" basic
```

Higher resolution:

```bat
run_all_extended.cmd "C:\workspace\solo\_projects\SST-Workbench\KnotPlot\KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0"
```

## Core falsification chain

```text
KnotPlot candidate
  -> blind ID + SHA-256 seal
  -> uniform arclength resample
  -> regularized Biot-Savart modal operator
  -> omega_m, d omega/dk
  -> tau_m = L/|v_g,m|
  -> Theta_m = omega_m tau_m
  -> preregistered D_m = 1 - cos(Theta_m)
  ---------------- FROZEN PREDICTION ----------------
  -> nonlinear paired perturbation evolution
  -> rigid-motion-aligned shape growth
  -> blind rank gate + global-gain holdout gate
  ---------------- SHA-256 FREEZE -------------------
  -> reveal KnotPlot preparation labels
```

## What is deliberately NOT allowed

- no per-knot fitting of delay;
- no per-mode fitting of delay;
- no choosing a favorable phase branch after seeing stability;
- no selecting `charge`, `bendforce`, `close`, etc. after reveal;
- no target fine-structure constant or particle observable in the solver.

## Native backend

`run_00_install.cmd` builds `sst_phase_delay_native` with MSVC/C++17 on Windows and stops if the imported backend is not C++.

The pure-Python backend exists for regression/debug only; campaign scripts require native C++.

## Status interpretation

`PASS` means the preregistered phase-delay score both anticorrelates with observed growth and a single globally calibrated gain improves untouched holdout prediction. It is evidence for this particular delayed self-feedback closure inside the numerical filament surrogate.

`FAIL` is scientifically useful: it means this simple swirl-clock stability mechanism does not explain the relaxation-matrix stability ordering under the chosen unforced dynamics.
