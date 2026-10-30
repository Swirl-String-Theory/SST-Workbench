# Finite-Core Spectral-Scale A/B/C Falsifier v0.1.0

**Status:** source-built, unexecuted scientific release. It is a *create-only generator kit* for the official **SST Falsifier Framework v1.1.0 / RC2**. It does not claim a successful new Euler or PKLSA experiment. A generated instance is self-contained because it contains the complete, hashed `_sst_runtime` created by the framework's **actual `tools/new_falsifier.py`**, not a shim imported from a mutable global Python installation.

## Research question

- **A — artifact/negative:** the previously identified `|m|=2` real-to-imaginary transition disappears or fails an adequately converged, preregistered search. **No promotion is not sufficient to assert A.** A limited `A_SUPPORTED_WITHIN_GRID_SCOPE` is issued only if both highest-resolution scans are native, have all Fourier quality gates passing, and contain no qualifying m=2 event; it is not an exhaustive no-go theorem.
- **B — spectral scale:** the same physical `|m|=2` C4-sector transition converges to a finite, dimensionless ratio `L/a = exp(q)` across spatial refinement, shell and finite-difference ladders. Even B does **not** prove dynamic preference for that cell size or global stability.
- **C — coupled hierarchy:** at least two independently converged and dynamically coupled scales reproduce across independent PKLSA providers/topologies with spatial and temporal convergence. Multiple Fourier peaks are *not* enough.

B and C are nested evidence levels, **not three mutually exclusive multiple-choice labels**. Model may return `UNRESOLVED` on all three.

## Prerequisites

- Your local `SST_Falsifier_Framework_v1.1.0_RC2` source folder (or an explicitly verified `v1.1.0` release), Python 3.14 environment, `numpy`, `pybind11`, `setuptools`, Windows C++ toolchain, with framework v1.1.0 report dependencies installed.
- A **new free A-series catalog ID** confirmed from the live `family_hierarchy.json` and `catalog_index.json`. The kit never invents or registers an ID and never modifies registry files.
- Optional for the C geometry pilot: installed `pklsa_bridge` Universal Atlas Adapter `v0.1.0` and **an existing verified E010 v0.4.0 consumer export folder**, containing `DATASET_MANIFEST.json` and `seeds/`. The huge main atlas ZIP is not copied.

### Create-only Windows installation

Set these according to your actual paths:

```bat
set "WB=C:\workspace\projects\SST-Workbench"
set "SST_WORKBENCH_ROOT=%WB%"
set "SST_PYTHON=%WB%\.venv\Scripts\python.exe"
set "FRAMEWORK=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.1.0_RC2"

"%SST_PYTHON%" create_instance.py --framework "%FRAMEWORK%" ^
  --catalog-id A076 ^
  --destination "%WB%\01_research\A_falsifiers\A076_finite_core_spectral_abc\A076-v0.1.0"
```

Replace `A076` with a **verified unallocated ID** (and update both occurrences). The creator refuses an existing output version directory and validates the 16-part report, science contract and gate plan before declaring the new instance ready.

For the optional C source pilot add:

```bat
  --dataset "C:\path\E010_VERIFIED_CONSUMER_EXPORT" --records RECORD_ID_1 RECORD_ID_2
```

The `--records` list must equal the export's exact ID list. To add different source groups later, prepare a separate E010 adapter export and release/version; do **not** silently change the frozen instance. The kit never selects best candidates by hidden target matching.

### Execute the resulting instance

```bat
cd /d "%WB%\01_research\A_falsifiers\A076_finite_core_spectral_abc\A076-v0.1.0"
run_all.cmd BACKEND_PREFLIGHT
run_all.cmd ATLAS_VERIFY
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
```

Run `ATLAS_VERIFY` only after setting `E010_ATLAS` and the pinned adapter, if applicable; an unavailable atlas must not be claimed `PASS`. A new run archives previous outputs instead of overwriting them. The framework writes a detailed LaTeX-derived PDF, evidence manifests, gate ledger, unique BLIND ZIP and SHA256. `run_all.cmd` adds an independent heartbeat in RC2.

`BASIC` is a smoke/research diagnostic. The full source retains `max_m=12` to preserve the original mode basis. `FULL` uses N64/96/128/160/192 at q=2.47..2.59 with 0.01 spacing, shell 2/3, h ladder and sensitivity to two other core kernels; this is intentionally heavy. A real native C++ backend is required for FULL: Python fallback cannot promote the model.

Only the original `v0.1.2.4` ring operator is used for ring claims. The corresponding `experiment/cpp/native.cpp` is copied byte-for-byte. Framework G10 runs two independent implementations of the **static regularized Biot-Savart subkernel**. It does not validate the full eigenproblem. The optional C PKLSA pilot measures static intercomponent Biot--Savart coupling, shape residuals and selected time-integration checks with original vertices; it **does not** directly establish a nonlinear hierarchy, nor substitute interpolation for spatial convergence.

## Output and provenance

Framework output folder: `./finite_core_spectral_abc_v0.1.0-outputs/`, automatically stamped and archived. Added raw cases: `abc_science/case_*.json`; decision ledger: `abc_science/ABC_VERDICT.json`; C pilot: `abc_science/C_PKLSA_DIAGNOSTICS.json` when applicable. The framework also writes `RUN_PROGRESS.jsonl`, `GATE_LEDGER.json`, hashes, and report/ZIP alongside the version folder. Private reveal keys must remain out of the BLIND archive.

## Scientific warnings

1. Periodic C4 mode projection applies to a circular ring, not an arbitrary knotted E010 curve.
2. A positive m=2 eigenpair change does not imply full-ring stability. The global spectral abscissa may still be positive.
3. The PKLSA v0.4.0 atlas has no completed dynamic scenarios; geometry intake is NOT an Euler equilibrium.
4. Different finite-core regularizations represent different model assumptions. A root's existence might be model dependent.
5. This release does not claim that the nonlinear separation coordinate L(t) is attracted to q*: that is a distinct G5 physical falsifier.
6. Results here are dimensionless numerical quantities, not calibrated seconds or metres.

## Package source and verification

`create_instance.py` uses the user's exact local framework at invocation and copies it via the official generator into the instance. This zip contains the complete legacy spectral Python source, its C++ kernel, scientific source code, 16-section report, configs, and synthetic logic regressions. Run `python -m pytest -q tests` from this kit before installation. `MANIFEST.sha256` lists archive source digests; the generated framework freeze creates an independent authoritative hash manifest.
