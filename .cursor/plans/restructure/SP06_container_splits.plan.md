---
name: SP06 container splits
todos:
  - id: t00
    content: "Split Maxwell / Einstein / Kelvin / Swirl Clock / Threaded Hole / Trefoil Lobe"
    status: pending
  - id: t01
    content: "Split remaining mixed roots (Hopf, routes, horn, GUI, Knot_Library, 3D, …)"
    status: pending
  - id: t02
    content: "Reveal keys under `keys/`; multi-junction roots where needed"
    status: pending
  - id: t03
    content: "Record `sst_trefoil_biot_py` diffs (no dedupe)"
    status: pending
  - id: t04
    content: "Done-criteria: all children accounted; provisional taxonomy resolved; baseline matches"
    status: pending
---
# SP06 — Ambiguous container splits

Status: `PLANNED` · Priority: P2 · Risk: medium · Depends on: SP05

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [ ] Split Maxwell / Einstein / Kelvin / Swirl Clock / Threaded Hole / Trefoil Lobe
- [ ] Split remaining mixed roots (Hopf, routes, horn, GUI, Knot_Library, 3D, …)
- [ ] Reveal keys under `keys/`; multi-junction roots where needed
- [ ] Record `sst_trefoil_biot_py` diffs (no dedupe)
- [ ] Done-criteria: all children accounted; provisional taxonomy resolved; baseline matches

**Next:** Blocked on SP05

Seventeen roots that each hold more than one thing. This is the phase that cannot be automated: a
script cannot tell a new hypothesis from a new software release. Every split below is a judgement,
recorded with its reasoning so it can be argued with later.

The scientific stake: **a new hypothesis or gate is not a new software version.** Registering SCII,
SCIIb and SCIII as "versions" of the Intrinsic Modal Swirl Clock asserts a lineage that does not
exist. That is a claim about the physics, made accidentally, by a directory layout.

## Rule for splitting

A child is its **own family** when it has an independent hypothesis, an independent gate, or an
independent code lineage. It is a **version** when it supersedes its predecessor for the same
question. It is a **variant** when it is the same version under a different configuration, blinding
state, or dependency pin.

When unsure, prefer a separate family. Merging two families later is cheap; unpicking a false
lineage after six months of citations is not.

---

## 1. `SST_Maxwell/` → six families

The clearest case. The numeric prefixes `1_` to `5_` were already an informal family index; this
just makes them real.

| From | To | Versions |
|------|----|---------:|
| `1_Maxwell_SST_Kinetic_Falsifier_v{0.1.0,0.2.0,0.3.0,0.3.1}` | `R/A/A011_maxwell_1_kinetic_energy/` | 4 |
| `2_Maxwell_SST_Dynamical_Field_Closure_Falsifier_v{0.1.0,0.2.0}` | `R/A/A015_maxwell_2_dynamical_field/` | 2 |
| `3_Maxwell_SST_Physical_Lines_Falsifier_v0.2.0` | `R/A/A012_maxwell_3_physical_lines/` | 1 |
| `3_SST_Maxwell_Blind_Falsifier_v0.1.0` | `R/A/A012_maxwell_3_physical_lines/` | 1 |
| `4_SST_Maxwell_Falsifier_v{0.1.0,0.2.0}` | `R/A/A013_maxwell_4_field_null/` | 2 |
| `5_{Maxwell_SST,SST_Maxwell}_Reciprocal_Falsifier_v{0.2.0,0.1.0}` | `R/A/A014_maxwell_5_reciprocal_figures/` | 2 |

Two unblind keys are **not** families — see §Reveal keys.

Note the naming inconsistency in family 5: `5_SST_Maxwell_Reciprocal_Falsifier_v0.1.0` and
`5_Maxwell_SST_Reciprocal_Falsifier_v0.2.0` swap the word order. They are the same family;
`FAMILY.yaml` records both legacy paths.

Watch out: `2_..._v0.2.0/` contains a `.venv`, and four Maxwell packs have absolute
`SST_WORKBENCH_ROOT` in `config/paths.cmd`. Convert those four to the SP01 resolver during this
split — they are the seven-file list from SP01, and this is the natural moment.

## 2. `SST_Intrinsic_Modal_Swirl_Clock/` → four families

| From | To | Versions |
|------|----|---------:|
| `SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v*` | `R/A/A035_intrinsic_modal_swirl_clock/` | 7 |
| `SST_SCII_Intrinsic_Modal_Phase_Swirl_Clock_Blind_Falsifier_v*` | `R/A/A036_scii_intrinsic_modal_phase_clock/` | 2 |
| `SST_SCIIb_Frozen_Modal_Pair_Subspace_Phase_Clock_Blind_Falsifier_v*` | `R/A/A039_sciib_frozen_modal_pair_phase_clock/` | 2 |
| `SST_SCIII_Koopman_DMD_Complex_Phase_Clock_Blind_Falsifier_v0.1.0` | `R/A/A040_sciii_koopman_dmd_phase_clock/` | 1 |

A032 carries the four-part identifiers `v0.2.2.5` and `v0.2.2.8`. They move unchanged; SP08
normalizes them.

A034's `sources.py` resolves four separate dataset roots
(`../../KnotPlot/knots/final`, `../../Ideal_Fremlin_Fseries/fremlin`, `../../Ideal_Sources`,
`../../Katlas_Sources_v0.2.2_Outputs`) and its config JSONs repeat them. This is the single densest
concentration of cross-pack paths in the repo — 193 files in the break-set. It is also the best
candidate for early resolver conversion, because converting one `sources.py` fixes the whole
family.

## 3. `SST_Threaded_Hole_Substrate_Blind_Falsifier_v0.1.0/` → two families

A root carrying a version suffix that contains two unrelated families. Both leave; the root
disappears entirely.

| From | To | Versions |
|------|----|---------:|
| `SST_Threaded_Hole_Substrate_Blind_Falsifier_v{0.1.0,0.1.1,0.2.0,0.2.1,0.3.0}` | `R/A/A024_threaded_hole_separatrix/` | 5 |
| `SST_Local_Thread_Texture_Boost_Invariance_Blind_Falsifier_v{0.1.0,0.2.0,0.2.1,0.2.2,0.3.0}` | `R/A/A025_local_thread_texture_boost/` | 5 |

The junction here is unusual: the old root name is `SST_Threaded_Hole_Substrate_Blind_Falsifier_v0.1.0`,
and old references reach *through* it to both families. A single junction cannot serve two targets,
so this root gets a **real directory** containing two junctions, one per family — the same
two-level pattern SP09 uses everywhere. Treat it as the rehearsal.

## 4. `SST_Trefoil_Lobe_Orientation_Blind_Falsifier/` → three families

The largest offender: 5,905 tracked files, 788 in the break-set, and only two of its twelve
children actually belong to the family the root is named after.

| From | To | Versions |
|------|----|---------:|
| `SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v{0.1.0,0.3.0}` | `R/A/A021_trefoil_lobe_self_confinement/` | 2 |
| `SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.*` | `R/A/A023_multitopology_rpo_floquet/` | 9 |
| `SST_Adaptive_Period_Aware_RPO_Multiple_Shooting_Floquet_Blind_Falsifier_v0.1.0` | `R/A/A031_adaptive_period_rpo_floquet/` | 1 |

A021's version names carry configuration: `v0.4.6_DD32_compact`,
`v0.4.7_HR_DD32_Ladder_compact`, `v0.4.8_Adaptive_Spectral_DD32_compact`. These move unchanged and
are normalized in SP08 to `v0.4.8/configs/adaptive-spectral-dd32-compact.json`.

Circular reference to break: `KnotPlot/KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0/run_80_sst_v048_preflight.cmd`
points at `SST_V048_DIR` with an absolute path into A021, and A021's own run scripts point back at
`SST_ATLAS_ROOT` in KnotPlot. Both must become `resolve_family()` calls before SP07 moves KnotPlot,
or the two junction layers will have to cover each other.

## 5. `SST_Einstein/` → two families

| From | To | Versions |
|------|----|---------:|
| `Einstein_SST_Blind_Falsifier_v0.1.0` | `R/A/A018_einstein_blind/` | 1 |
| `Einstein_SST_Emergent_Metric_Poisson_Closure_Gates_v{0.1.0,0.1.1}` | `R/A/A017_einstein_emergent_metric_poisson/` | 2 |

`Einstein_SST_Emergent_Metric_Poisson_Closure_Gates_v0.1.1/` contains a directory of its own name —
a nested self-copy. Confirm it is a duplicate before moving; if so it goes to `09_archive/`, not
into the family.

## 6. `SST_Kelvin_Floquet/` → three families, two domains

| From | To | Versions |
|------|----|---------:|
| `Kelvin_Kirchhoff_SST_Falsifier_v{0.1.0,0.1.1}` | `R/A/A019_kelvin_kirchhoff_evanescent_core/` | 2 |
| `Kelvin_Joule_SST_Transient_Energy_Falsifier_v0.1.0` | `R/A/A032_kelvin_joule_transient_energy/` | 1 |
| `SST_Kelvin_Floquet_Workbench_cpp_pybind_v{0.1.0,0.1.1}` | `R/C/C008_kelvin_floquet_workbench/` | 2 |

The third is a workbench, not a falsifier — it goes to `C_dynamics`. This is the split that most
justifies the letter layer: three things sharing a root, two domains apart.

`Kelvin_Kirchhoff_SST_Falsifier_v0.1.0/` also contains a nested self-named directory. Same check as
§5.

## 7. `SST_Hopf_Benchmark/` → two families

| From | To | Versions |
|------|----|---------:|
| `SST_Hopf_Benchmark_Packet_v0.1` | `R/D/D005_hopf_benchmark/` | 1 |
| `SST_Hopf_cpp_pybind_v{0.1.0,0.1.1,0.1.3,0.1.4}` | `R/D/D005_hopf_benchmark/` | 4 |

## 8. `SST_chi_phase_research/` → two families

| From | To | Versions |
|------|----|---------:|
| `sst_chi_phase_package_v1{0B1,1B0,2B0,3B0,4B0,5B0,6B0}` | `R/C/C001_chi_phase_track_b/` | 7 |
| `sstcore_chiE_local{0,_v4,_v5,_v6,_v7}` | `R/C/C002_chi_e_biot_savart/` | 5 |

The `v16B0` identifiers are the "Track B" numbering and carry meaning. They move unchanged; SP08
decides whether to map them onto semver or leave them as a documented exception. Leaving them is
acceptable — this is a closed historical series.

Related: `SST_Trefoil_Closure/` contains `sst_chi_phase_package` v1–v6, the *predecessor* of this
series. See §14.

## 9. `SST_v0_8_19_routes_research/` → five families, three domains

| From | To |
|------|-----|
| `SST_v0_8_19_Planck_Routes_A_to_D_equivalence_corrected_pack` | `R/B/B002_planck_routes_a_to_d/` |
| `SST_v0_8_19_Planck_Routes_v3_preregistered_all_inclusive_pack` | `R/B/B002_planck_routes_a_to_d/` |
| `SST_v0_8_19_RouteA_parallel_derivation_falsification_pack` | `R/A/A001_route_a_parallel_derivation_falsification/` |
| `sst_torsion_impedance_pybind11_v0.8.19_autobuild` | `R/C/C004_torsion_impedance/` |
| `sst_nonfit_prediction_harness_v0_8_19` | `R/A/A002_nonfit_prediction_routes_control/` |

B004 contains the two longest paths in the repository, both 231 characters, under
`archive/legacy_extracted_v2_corrected_pack/canon_patches/`. Verify `core.longpaths` from SP03 is
active before moving this one.

## 10. `SST_horn_bem_research/` → two families

| From | To |
|------|-----|
| `sst_horn_dirichlet_package` | `R/B/B003_horn_bem/` |
| `sst_horn_neumann_bem_package`, `sst_horn_neumann_bem_all_audits` | `R/B/B003_horn_bem/` |

`_all_audits` is a variant of the package, not a separate family: same boundary condition, same
question, broader audit set. It goes to `B007/variants/all_audits/`.

## 11. `SST_ideal_trefoil_biot_research/` → two families plus a library

Resolved by inspection. `sst_trefoil_bs/` holds six files — `sst_bs_kernel.cpp`, `build.py`,
`ideal_source.py`, `trefoil_energy.py` and a figure. Nothing imports it as a package and it defines
no falsification gate. It is reusable numerics filed as research.

| From | To |
|------|-----|
| `sst_ideal_trefoil_biot_package_v2` | `R/C/C003_ideal_trefoil_biot/` |
| `sst_3d_collider_robust` | `R/C/C005_3d_collider/` |
| `sst_trefoil_bs` | `L/D/D001_trefoil_biot_savart_kernel/` |

### The real shared module, and why it does not move

`sst_trefoil_biot_py.py` and `sst_trefoil_biot_build.py` exist as **six copies each**:

```text
SST_chi_phase_research/sstcore_chiE_local0/
SST_chi_phase_research/sstcore_chiE_local_v4/
SST_chi_phase_research/sstcore_chiE_local_v5/
SST_chi_phase_research/sstcore_chiE_local_v6/
SST_chi_phase_research/sstcore_chiE_local_v7/
SST_ideal_trefoil_biot_research/sst_ideal_trefoil_biot_package_v2/
```

At least eight files import them, across C001, C002 and C003.

**Do not deduplicate.** Each version pinned its own copy; collapsing them would change what those
versions compute, which is precisely what SP10 exists to prevent. Instead:

1. Diff the six copies and record in `10_docs/architecture/` whether they have diverged. If they
   have, that divergence is a scientific fact about those versions, not a maintenance error.
2. Promote the newest copy to `L/D/D002_trefoil_biot_py/` for new work only.
3. Leave every version's copy exactly where it is.

`sst_trefoil_bs/ideal_source.py:45` uses `parents[2]` to reach the workbench root. That becomes
`sst_workbench_paths.WORKBENCH_ROOT` when the kernel moves to the library domain.

## 12. `SST_Route_I_relative_entropy_PoC/` → two families

| From | To |
|------|-----|
| `SST_Route_I_relative_entropy_PoC_v0.0.4` | `R/F/F002_route_i_relative_entropy_poc/` |
| `routeI_heat_guard_patch_bundle_v0_8_19` | `R/F/F002_route_i_relative_entropy_poc/variants/` |

Most of this family exists only inside `Restore_Archives/Route_I/` (12 zips). Record in
`FAMILY.yaml` that only v0.0.4 is extracted; do not unpack the rest.

## 13. `SST_QHP_Stability_Landscape/` → two domains

| From | To |
|------|-----|
| `SST_QHP_Stability_Landscape_Blind_Falsifier_v{0.1.0,0.1.3}` | `R/A/A034_qhp_stability_landscape/` |
| `SST_KnotPlot_QHP_Sweep_Generator_v0.1.0` | `T/A/A003_knotplot_qhp_sweep_generator/` |

A generator and the falsifier that consumes its output are not versions of each other. The
generator's output lands in `03_data/D_generated/qhp/`, which SP07 also feeds — coordinate
the two.

## 14. `SST_Trefoil_Closure/` → one existing family, one new, plus outputs

Resolved: the early `sst_chi_phase_package` v1–v6 **is** the Track B family. One continuous
lineage, not two.

| From | To |
|------|-----|
| `sst_chi_phase_package`, `_v2` … `_v6` | `R/C/C001_chi_phase_track_b/` (early versions) |
| `sst_taxonomy_starter_v2`, `_v3b` | `R/F/F004_taxonomy_starter/` |
| `multisector_fit_results/`, `exports/`, `phi-3_1/` | `03_data/D_generated/` |
| `build/` | delete (SP11) |
| `_dashboard_conflict/`, `archive/` | `09_archive/` |

C001 therefore spans two current roots and is assembled from both in the same commit. Its version
series runs `v1 … v6` (from here) then `v10B1 … v16B0` (from `SST_chi_phase_research/`). The gap
between v6 and v10B1 is real and is recorded in `FAMILY.yaml` rather than papered over — v7 to v9
are not in the working tree and may only exist in `09_archive/restore/ChiPhase/` (34 zips).

Check that archive bucket before declaring the series complete.

## 15. `GUI/` → three apps, one research family, plus assets

| From | To |
|------|-----|
| `vortexring-lab/` | `APP/A003_vortexlab/monolith/` |
| `vortexlab-modular-v7.6.25b-m1/` | `APP/A003_vortexlab/modular/` |
| `coils/` | `APP/A002_coil_gui/` |
| `SST_Math_Lab_v0.2.0/` | `APP/A004_math_lab/v0.2.0/` |
| `images/` | `03_data/C_reference/C002_gui_images/` |
| `additional for Vlab/` | `R/C/C006_uq_twisted_vortex_ring/` |

### `additional for Vlab/` is a research pack

Not an asset set. Seven files implementing a self-contained physics experiment: `axisym_solver.py`
integrates the axisymmetric incompressible Euler equations with swirl on a 256x512 grid to measure
the ring-speed deficit of a twisted vortex ring, fixing the Kirchhoff twist-stiffness prefactor
`C_eff` and discriminating a Rankine core from a hollow core. With `run_experiment.py`,
`collect_and_plot.py`, `tier1_static_checks.py`, `results_table.csv` and a figure.

Its README records a status upgrade from "derived" to "numerically verified", and closes with port
notes for the VortexLab simulator — which is the only reason it sits under `GUI/`. It moves to
`C_dynamics` and gets a real family with its own `FAMILY.yaml`.

### A003 is one app with two architectural lines

`vortexlab-modular-v7.6.25b-m1/` is the modular rewrite of `vortexring-lab/`, not a second app:
a monorepo with `apps/web`, `packages/contracts` and `packages/sstcore-adapter`.

But the rewrite is incomplete and the monolith is still where work happens:

| | monolith | modular |
|---|---:|---:|
| `.glsl` shaders | 13 | 0 |
| newest file | 2026-09-03 | 2026-08-13 |

So `FAMILY.yaml` records `latest` on the monolith line and the modular line as
`successor: in-progress`. Do **not** set `latest` to the modular line — it would point every
consumer at a build with no rendering layer. Revisit when the shaders are ported.

`vortexring-lab/` also contains `node_modules/` (ignored, but bulky) and
`inbox_from_to_be_processed/`, a relocation artifact that should be resolved rather than carried
forward. That inbox holds `validate_trefoil_sampler.py` and `validate_ideal_knots.py`, which import
`sst_trefoil_biot_py` — the shared module discussed in §11. They belong with C003, not with an app.

**The casing fix from SP03 must be committed before this move.** Renaming and re-casing in one step
produces a tree with both `gui/` and `GUI/`.

## 16. `Knot_Library/` → library plus data

| From | To |
|------|-----|
| `SST_Knot_Library/SST_Knot_Library_v0.2.{0,2,3,4,5}` | `L/B/B001_knot_library/` |
| `Sources/`, `Derived/`, `Registry/`, `Quarantine/` | `03_data/A_knots/A007_knot_library_sources/` |

`library_root.py` in v0.2.0 is the model SP01 generalized. After this move it should *use* the
shared resolver rather than keep its own copy — the first real consumer, and a good test.

## 17. `3D/` → tool plus generated data

| From | To |
|------|-----|
| `3D/**/*.py`, `.scad`, source models | `T/C/C001_3d_models/` |
| `3D/**/*.stl`, `3D/Python/3d_sliced/*.gcode` | `03_data/D_generated/D001_3d_exports/` |

~2.5 GB of the 2.59 GB is generated output. `.stl` and `.gcode` are already gitignored, so most of
this is a filesystem move with no index change. Verify before assuming.

## 18. `experiments/`

| From | To |
|------|-----|
| `experiments/sycl/*.cpp` | `04_tools/D_compute/sycl_probes/` |
| `experiments/derive_constants/`, `experiments/trefoil/` | stubs — delete in SP11 |

---

## Reveal keys

Reveal and unblind keys are variants of a version. They never become families and never become
versions.

| Current | Destination |
|---------|-------------|
| `SST_Maxwell/3_Maxwell_SST_Physical_Lines_Unblind_Key_v0.2.0/` | `A013_.../keys/v0.2.0_UNBLIND_KEY/` |
| `SST_Maxwell/3_SST_Maxwell_Blind_Unblind_Key_v0.1.0/` | `A014_.../keys/v0.1.0_UNBLIND_KEY/` |
| `SST_Quantum_Galileo_..._v0.1.1_REVEAL_KEY/` | `A039_.../keys/v0.1.1_REVEAL_KEY/` (moved in SP05) |

`keys/` is gitignored per SP03. Blind and revealed artifacts are never merged.

## Tests to write

- `test_container_split.py` — for each split root: every child is accounted for in exactly one
  destination; no child is silently dropped; the sum of child counts before equals the sum after.
- `test_no_cross_family_versions.py` — no family directory contains a version whose name belongs to
  another family's naming prefix. This is the regression test for the Threaded Hole class of fault.
- `test_multi_junction_root.py` — for roots that become a real directory holding several junctions
  (§3), every old child path resolves.
- `test_keys_not_versions.py` — nothing under `keys/` or `variants/` is counted as a version by
  `workbench_tree.py`.

## Rollback

Per split root, not per child. A partially-split container is the worst possible state: half the
children moved, junctions covering some paths but not others. Either the whole root splits and
verifies, or it is reverted whole.

## Done criteria

- All seventeen roots split, every child accounted for.
- The one remaining `provisional` entry, `F007_taxonomy_starter`, resolved in writing. The other
  four were settled before this sub-plan started; see [CATALOG_v0.1.md](CATALOG_v0.1.md)
  §Changes since first draft.
- The six `sst_trefoil_biot_py` copies diffed and their divergence recorded, with **no copy
  deleted**.
- `09_archive/restore/ChiPhase/` checked for C001 versions v7 to v9, and the result recorded in
  `FAMILY.yaml` either way.
- Multi-junction roots verified: every old child path resolves.
- Each new family has a `FAMILY.yaml` stub with `legacy_paths` naming its pre-split location.
- Test suite matches the SP00 baseline.
