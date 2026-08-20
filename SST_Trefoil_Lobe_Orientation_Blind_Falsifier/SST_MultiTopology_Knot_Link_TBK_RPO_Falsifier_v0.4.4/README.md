# SST Multi-Topology Knot/Link TBK + RPO/Floquet Blind Falsifier v0.4.4


## v0.4.4 Windows/Intel Arc SYCL architecture

Windows diagnostics demonstrated a reproducible `0xC0000005` during CPython import of `.pyd` files containing real SYCL device kernels, while bind-only `-fsycl` modules imported normally. v0.4.4 therefore keeps Python/pybind host-only and runs device kernels in a persistent standalone `build\sst_sycl_worker.exe`.

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

It also contains both full local source archives and the canonical selected panel inputs. `MANIFEST.sha256`, `release_history/INDEX.sha256`, and reproducibility-input hash manifests allow byte-level verification.

See `docs/PREREGISTRATION_MULTI_TOPOLOGY.md`, `docs/PANEL_REFERENCE_CONCLUSIONS.md`, `docs/REPRODUCIBILITY.md`, and `CHANGELOG.md`.
