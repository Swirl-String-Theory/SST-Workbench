# A074-v0.3.0 — Finite-core Euler Trefoil Equilibrium Qualification

**Release status:** DEVELOPMENT / P1–P3 only. **Framework:** 1.1.0 RC2 (source validated; target Windows hardware certification outstanding). **No physics, stability, maximum force, or GR comparison claim.**

## Source and changes

- Original Gilbert trefoil `3:1:1` Fourier record is copied from A074 v0.2.0 unchanged, with source hashes recorded.
- P1: load **exact** `EQUILIBRIUM_SEARCH.json` supplied from the user's A074 v0.2.0 local run. Re-use the selected geometric parameters and core for ALL computations; do not reoptimize during the independent grid check.
- P2: unforced 3-D incompressible Euler velocity, projected vorticity field, and **full-field vorticity-relative-stationarity** least squares, removing rigid translation and rotation. This is *not* the centerline-only marker score and not a certified globally periodic rotating equilibrium.
- P3: fixed final time 0.1 s; spatial grids 32/48/64 quick and 96/128/192 extended. Core support and smallest nonlocal free gap have independent resolution gates; time refinement separately performed on 48^3. The 0.28 m core in 6 m box is underresolved on the quick grid set.
- No load, perturbation stability or force-to-failure trajectories in this tranche. The prior v0.2.0 results are **not** reinterpreted as new positives.

## Framework 1.1.0 operational change

The instance contains `_sst_runtime/` with byte-level SHA-256 verification and no global fallback. This is the checked RC2 Python runtime subset used by the instance; native and GPU Euler solvers are not certified. `run_all.cmd FULL` must **exit 3** when only the genuine Python science backend was executed. A native C++ Biot-Savart template is not an independent Euler backend. A complete framework 2-of-3 certification therefore remains blocked (no fake PASS).

For the custom P1–P3 qualification (does not require native/GPU):

```bat
python -m pip install -r requirements.txt
run_tests.cmd
run_qualification.cmd --grids 32,48,64
run_qualification_extended.cmd
```

For the Framework 1.1.0 pipeline (only after validating report / contracts):

```bat
run_all.cmd BACKEND_PREFLIGHT
rem ATLAS_VERIFY is optional and not used: this tranche is deliberately Gilbert-only.
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
```

Framework may intentionally exit nonzero for hardware/backend admission. `FREEZE` is create-once. E010 atlas is disabled for this specific local Gilbert-only tranche (no speculative claim of an E010 independent source). `run_qualification_extended.cmd` can be memory- and compute-intensive. Do not reuse a scientific status from a failed/resolution-limited run.

Outputs go in `A074_Max_Transfer_Force_Trefoil_v0.3.0-outputs/` and archive is generated separately with `.sha256`. The report is `../A074_v0.3.0_P1P3_Qualification_Report.pdf` in this delivered package context.

## Equations

In the rotating frame of a genuinely localized full field, the stationarity residual is

\[
\mathcal R_\omega=\frac{\min_{U,\Omega}\|\partial_t\omega+(U+\Omega\times r)\cdot\nabla\omega-\Omega\times\omega\|_{2}}{\|\partial_t\omega\|_{2}}.
\]

A rigidly rotating state is not globally periodic. Consequently, this metric is diagnostic, not a proof of a periodic Euler relative equilibrium. Spatial gates require at least eight grid cells per core radius and three cells across the free nonlocal inter-core gap. These are preregistered conservative thresholds, not theorems.

**Distribution:** The public BLIND ZIP excludes private nonce/key files. Restore the separately supplied PRIVATE (NOT REVEALED) ZIP into the same `A074-v0.3.0` directory if executing the framework freeze/blind-commitment workflow on Windows. Protect that archive. A verified 6-page PDF comes as a separate download.
