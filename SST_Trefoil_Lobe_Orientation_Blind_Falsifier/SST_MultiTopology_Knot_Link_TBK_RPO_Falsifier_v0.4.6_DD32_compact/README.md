# SST Multi-Topology Knot/Link TBK + RPO/Floquet Blind Falsifier v0.4.6.1


> **v0.4.6.1 maintenance fix:** the accelerated finite-difference Jacobian is explicitly total-only. Component-decomposition diagnostics remain base-state diagnostics; this prevents empty `local/self_nonlocal/mutual` lists from entering `_shape_project()` while preserving GPU acceleration and all scientific gates.

## Experimental Arc DD32 / FP32x2 backend

v0.4.6 adds a double-single GPU path for Arc GPUs without native FP64.  A scalar is carried as two FP32 values, `hi + lo`; this targets roughly 48 significand bits in favorable cases but is **not IEEE FP64**.

First run:

```bat
run_sycl_dd32_smoke.cmd
```

The smoke measures ordinary FP32 and DD32 against the CPU/Python FP64 reference and must pass before the DD32 archive launchers continue.  If it passes, try:

```bat
run_archive_extra_extended_sycl_dd32.cmd
run_archive_full_sycl_dd32.cmd
```

See `docs\DD32_FP32X2.md`.  CPU/OpenMP FP64 remains the reference for final scientific claims until full campaign parity is demonstrated.

---

## v0.4.5.4 SYCL host/runtime isolation

The Arc worker remains a standalone persistent process.  In explicit `*_sycl.cmd` campaigns, CPython now imports the host/OpenMP `_native.pyd` **without** registering the oneAPI DLL tree.  oneAPI DLL search registration is reserved for the legacy unsafe in-process SYCL extension only.  This isolates MSVC/OpenMP host kernels from the Intel SYCL runtime after `setvars.bat`.

Expected campaign startup after the worker parity smoke:

```text
[SST] initializing host native support for backend=sycl
[SST] host native loaded=True; probing external SYCL worker=True
[SST] backend initialization complete: sycl_worker=True device=Intel(R) Arc(TM) A770 Graphics
[SST] campaign backend=sycl datasets=127 ...
[SST] [001/127] B01 START
```


## v0.4.4 Windows/Intel Arc SYCL architecture

Windows diagnostics demonstrated a reproducible `0xC0000005` during CPython import of `.pyd` files containing real SYCL device kernels, while bind-only `-fsycl` modules imported normally. v0.4.4 therefore keeps Python/pybind host-only and runs device kernels in a persistent standalone content-addressed `build\sst_sycl_worker_<hash>.exe`.

Validate the worker first:

```bat
run_sycl_worker_smoke.cmd
```

On an Arc A770 (no native FP64), `run_archive_*_sycl.cmd` is **FP32 screening only**. Confirmatory FULL remains:

```bat
run_archive_full.cmd
```

See `docs\SYCL_WORKER_ARCHITECTURE.md`.

---

## Complete archive EXTRA_EXTENDED / FULL campaigns

This release runs the generic knot/link falsifier over **all 127 bundled local geometries**: 78 Fremlin `.fseries` files (including every variant suffix) and 49 KnotPlot/RidgeRunner final knots, unlinks, links and torus objects.

### Recommended commands

```bat
run_archive_inventory.cmd
run_archive_validate.cmd
run_archive_extra_extended.cmd
run_archive_full.cmd
```

For a long FULL run split into deterministic chunks:

```bat
run_archive_full_sharded.cmd 8
```

For Intel Arc / oneAPI SYCL:

```bat
run_archive_extra_extended_sycl.cmd
run_archive_full_sycl.cmd
```

If a run is interrupted, reuse the exact output directory:

```bat
run_archive_resume.cmd full outputs_archive_full_YYYYMMDD_HHMMSS_mmm
```

Each completed archive run adds `ARCHIVE_CONCLUSIONS.md`, while the existing `REPORT.md`, `GATE_CONCLUSIONS.md`, `COMPARATIVE_CONCLUSIONS.md`, `summary_metrics.csv`, blind hashes and per-dataset arrays remain available.

---

# SST Multi-Topology Knot/Link TBK + RPO/Floquet Blind Falsifier v0.4.0

v0.4.0 generalizes the v0.3.0 trefoil-only falsifier to a blinded comparative panel of knots, unknots, links, unlinks and torus links while retaining the full historical release chain.

## Canonical BASIC panel

The bundled panel contains 17 independent geometry inputs:

- unknot: Fremlin `1_1` (mapped to `0_1`) and KnotPlot/RidgeRunner `knot_0.1`;
- trefoil: Fremlin `3_1`, KnotPlot/RidgeRunner `knot_3.1`, and `torus_2.3`;
- figure-eight: Fremlin and KnotPlot/RidgeRunner `4_1`;
- `5_1`: Fremlin and KnotPlot/RidgeRunner;
- `5_2`: Fremlin and KnotPlot/RidgeRunner;
- unlink controls: `link_0.2.1`, `link_0.3.1`;
- Hopf-like control: `link_2.2.1`;
- three-component links: `link_6.3.1`, `link_6.3.3`;
- three-component torus link: `torus_6.9`.

The original source archives are also bundled under `repro_inputs/source_archives/`, so a broad survey can be rerun later without relying on external files.

## Scientific decomposition

For every component the regularized Biot--Savart velocity is decomposed into

- `local` -- neighboring same-component segments;
- `self_nonlocal` -- distant segments of the same component;
- `mutual` -- all other components (zero for one-component knots);
- `total` -- their sum.

The generic reduced basis is topology-agnostic:

- breathing: low-order normal displacement;
- torsion-sensitive: first-harmonic binormal displacement;
- Kelvin-like: higher normal/binormal Fourier modes.

This generic basis is **complementary to** the v0.3.0 trefoil-specific three-lobe basis. A v0.4 `P2` result must not be presented as a re-evaluation of v0.3 `G2`; the two tests span different perturbation subspaces.

## Gates

- `P0_geometry_core_clear` -- tube-thickness/core-radius clearance is above the preregistered margin.
- `P1_jacobian_converged` -- reduced Jacobian converges over the preregistered epsilon ladder.
- `P2_linear_growth_bounded` -- no strong growing reduced mode in the generic basis.
- `P3_nearest_relevant_separates` -- nearest self-nonlocal (knot) or mutual (link) pair is separating initially.
- `P4_TBK_collective_stabilizes` -- cross-family TBK coupling reduces the dominant growth rate relative to a block-diagonal counterfactual.
- `P5_short_ringdown_bounded` -- finite perturbation remains bounded and core-clear over the short campaign.
- `P6_linking_preserved` -- for multi-component objects, pairwise Gauss linking is conserved within tolerance.
- `P7_RPO_recurrence` -- a genuine excursion followed by a return is found.
- `P8_Floquet_bounded` -- evaluated only after `P7`; non-neutral Floquet multipliers remain inside the preregistered bound.

`P0`, `P1`, `P2`, and `P5` define the per-dataset BASIC/EXTENDED classification. Other gates are diagnostic/causal.

## Commands

Install and compile the C++/OpenMP backend:

```bat
run_install.cmd
```

Canonical 17-input BASIC panel:

```bat
run_panel_basic.cmd
```

Higher-resolution panel with Kelvin harmonics 2, 3 and 4:

```bat
run_panel_extended.cmd
```

Full bundled archive survey (fast screening basis, no RPO):

```bat
run_archive_survey.cmd
```

Install + BASIC + EXTENDED:

```bat
run_all.cmd
```

Historical trefoil-only conclusions can be recomputed with:

```bat
run_reproduce_history_basic.cmd
run_reproduce_history_extended.cmd
```

## Output reports

Each panel writes:

- `REPORT.md`
- `GATE_CONCLUSIONS.md` -- conclusion and evidence per gate and input
- `COMPARATIVE_CONCLUSIONS.md` -- post-unblind ranking and link diagnostics
- `summary_metrics.csv`
- `pre_unblind/Bxx_analysis.json`
- `pre_unblind/Bxx_arrays.npz`
- `pre_unblind/blind_verdict.json`
- `unblind_manifest.json`
- `final_verdict.json`

## Reproducibility

v0.4.0 contains the exact older release ZIPs:

- v0.1.0
- v0.1.1
- v0.2.0
- v0.3.0

It contains both full local source archives and the canonical selected panel inputs. From v0.4.5.3 onward, `release_history/` is compact: one exact v0.4.1 scientific capsule is embedded, while later runtime-only releases are recorded by SHA-256 plus changelog rather than recursively nested ZIPs. `MANIFEST.sha256`, `release_history/INDEX.sha256`, `release_history/HISTORICAL_HASHES.sha256`, and reproducibility-input hash manifests provide byte-level verification.

See `docs/PREREGISTRATION_MULTI_TOPOLOGY.md`, `docs/PANEL_REFERENCE_CONCLUSIONS.md`, `docs/REPRODUCIBILITY.md`, and `CHANGELOG.md`.


## v0.4.5.3 Windows worker lock fix

A successful smoke can briefly leave the worker image mapped on Windows. Earlier launchers then forced a rebuild to the exact same `build\sst_sycl_worker.exe`, allowing `link.exe` to fail with `LNK1104`. v0.4.5.3 uses a content-addressed worker name based on source/build flags/compiler fingerprint, compiles to a unique temporary EXE, and reuses an existing matching worker instead of overwriting it. The SYCL campaign scripts no longer request `--force`. Scientific settings are unchanged.


## v0.4.5.1 maintenance fix

`tools\build_sycl_worker.py` and `tools\sycl_worker_smoke.py` now prepend the project root to `sys.path` before importing `native_ext`. This fixes `ModuleNotFoundError: No module named 'native_ext'` when the tools are launched directly by `run_sycl_worker_smoke.cmd`. No scientific configuration, gate, threshold, dataset, or numerical method changed.

## v0.4.5 progress/runtime behavior

`run_all.cmd`, `run_panel_basic.cmd` and `run_panel_extended.cmd` now print a blind progress line for every dataset. A long calculation therefore no longer looks frozen. `--backend auto` is intentionally CPU/OpenMP FP64 and does not inspect or start the external SYCL worker; GPU use is explicit via the `*_sycl.cmd` launchers. Scientific configs and gates are unchanged from v0.4.4.


## v0.4.5.3 compact archive

The old recursive `release_history` policy grew the package exponentially (v0.4.5.2 exceeded 250 MB). v0.4.5.3 retains only the exact v0.4.1 scientific capsule (~4.4 MB), because that capsule already contains v0.1.0--v0.4.0. Runtime-only v0.4.2--v0.4.5.2 artifacts are represented by hashes and the changelog. Full Fremlin/KnotPlot source archives remain bundled. Scientific code and configs are unchanged from v0.4.5.2.
