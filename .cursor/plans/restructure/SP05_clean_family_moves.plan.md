---
name: SP05 clean family moves
todos:
  - id: t00
    content: "Pilot A038 trefoil dynamic seed qualification (full run + output hash)"
    status: pending
  - id: t01
    content: "Move remaining clean families (version names unchanged)"
    status: pending
  - id: t02
    content: "Stub `FAMILY.yaml` per family"
    status: pending
  - id: t03
    content: "Place variants/keys correctly (no new catalog IDs)"
    status: pending
  - id: t04
    content: "Route-B last (shared outputs split rows)"
    status: pending
  - id: t05
    content: "Done-criteria: families at catalog paths; SHA junctions; ≥5 packs run via old paths"
    status: pending
---
# SP05 — Clean family moves

Status: `PLANNED` · Priority: P1 · Risk: medium · Depends on: SP04

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [ ] Pilot A038 trefoil dynamic seed qualification (full run + output hash)
- [ ] Move remaining clean families (version names unchanged)
- [ ] Stub `FAMILY.yaml` per family
- [ ] Place variants/keys correctly (no new catalog IDs)
- [ ] Route-B last (shared outputs split rows)
- [ ] Done-criteria: families at catalog paths; SHA junctions; ≥5 packs run via old paths

**Next:** Blocked on SP04

Thirty-three roots where the directory already equals exactly one research family. The root is
renamed to its catalog family directory; version directories inside keep their current long names
until SP09.

## Result shape

```text
SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier/     (junction)
        |
        v
01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/
├── FAMILY.yaml                                            (stub here, completed in SP08)
├── SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.1.0/
├── SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.1.1/
├── ...
└── variants/
    └── v0.3.0+knotlib0.2.5/
```

Note what has **not** happened: version names are untouched, so a junction at the old root makes
every old path valid again, character for character. That is the whole reason stage 1 and stage 2
are separate.

## The pilot

`SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier` → `A037`. It is the right first family:

- Clean consecutive series `v0.1.0 … v0.3.1`, seven versions.
- 401 tracked files — large enough to be real, small enough to inspect.
- Only 34 files in the break-set.
- One anomaly worth exercising the variant rule on:
  `SST_Trefoil_v0.3.0_with_Knot_Library_v0.2.5` is a *variant* of v0.3.0, not a version. It goes to
  `variants/v0.3.0+knotlib0.2.5/` and is recorded in `FAMILY.yaml`.
- It references `..\..\Knot_Geometry_Library\...` in `run_all_smoke.cmd` and
  `Fremlin_FourierSeries/fremlin/3_1/...` in `src/sst_seed_falsifier/atlas.py`, so it exercises
  cross-family junctions created in SP04.

**Do not proceed past the pilot until it passes a full run**, not just an import check. Install,
build the native backend, basic run, compare the output manifest hash to a pre-move run of the same
version. If that fails, the problem is the method, not the family.

## The thirty-three

Full destinations in [RESTRUCTURE_PLAN_v0.1.plan.md](RESTRUCTURE_PLAN_v0.1.plan.md) §2. Grouped by risk:

**Group A — single version, trivial** (5): `SST_6Source_Blind_Falsifier_v0.1.0`,
`SST_Breathing_Stretching_Return_Phase_Causality`, `SST_Sutcliffe_HSS_feasibility_gate`,
`SST_dark_knot_rayleigh_research`, `Trefoil_Balance_to_TBK_RPO_Handoff_v0.1.0`.

**Group B — clean multi-version** (18): the pilot plus `SST_7Article_Closure_Holonomy`,
`SST_Chiral-Kelvin-Mode`, `SST_Chirality_Helicity_Transport_Polarity`,
`SST_contact_billiard_hydrodynamic_falsifier`, `SST_counterpulley_alpha_falsifier`,
`SST_dimensionless_dynamic_predictions`, `SST_Finite_Core_Axial_Toroidal_Phase_Delay`,
`SST_Fourier_vs_Ideal_Blind_Falsifier`, `SST_Helmholtz`, `SST_Material_Phase_EFT`,
`SST_minimal_falsification_harness`, `SST_Phase_Feedback_Delay_Knot_Stability`,
`SST_preferred_frame_binary_falsifier`, `SST_Quantum_Galileo_Action_Gauge_Closure`,
`SST_ssdl_audit_research`, `SST_vArrow_Spectral_Blind_Falsifier`, `SST21D_knot_order_pipeline`,
`Wien_Planck_SST_Field_Matter_Closure`.

**Group C — non-standard version identifiers** (7): `SST_Coil_DigitalTwin_research`
(`v10_complete_restored`, `v8_exact_rodin`), `SST_CoilLab_research` (`v2_work`),
`SST_contra_swirl_bridge_research` (`v0_2`, `v0_6`), `SST_fermat_pybind_research`
(`v0.4.3_flat`), `SST_ideal_links` (`v0.2.1.1`, `v0.4.0-alpha.1`),
`Independent_FiniteCore_SpectralSelector` (`v0.1.2.4`), `SST_Katlas_Link_Geometry_Conditioning_v2.0.0`.

Group C moves with names **unchanged**. Normalizing `v0.1.2.4` to `v0.1.2` + `revision: 4` is SP08
and SP09's job, and doing it here would conflate two independent risks.

**Group D — unversioned or mixed** (3): `SST_derive_constants_research` (topic subdirectories, no
versions), `SST_fs_attachment_audit_research` (code mixed with eleven output directories),
`SST_timefield_spectral_v06_research` (output-only, goes to `03_data/D_generated/`).

Group D needs a source/output separation decision per directory before moving. Outputs go to
`03_data/D_generated/`; source goes to the family. Record the split in `path_map.csv` as separate
rows.

**Special: `SST_routeB_RT_bem_research`** (22 versions plus `demos/`, `knot-data/`, `outputs/`,
`shared/`). 7,144 tracked files, second-largest in the repo. Four rows: versions to
`01_research/B_closures/B002_route_b_rt_bem/`, `outputs/` and `shared/` to
`03_data/D_generated/D004_routeb_shared_outputs/`, `knot-data/` to `03_data/A_knots/`, `demos/`
stays with the family. Move it **last** in this phase.

## Per-move procedure

As SP04, plus two additions:

- Write a stub `FAMILY.yaml` with `catalog_id`, `name` and `legacy_paths`. `latest` and `status`
  are filled in SP08 — a stub now means SP08 has something to validate against rather than
  generate blind.
- For any family with a `variants/` or `keys/` entry, create those directories and move the
  variant in the same commit as the family. A variant separated from its family across two commits
  is how variants get lost.

## Tests to write

- `test_family_move.py` — after each move: the family directory exists at its catalog path; every
  version directory that existed before still exists with its exact original name; the junction
  resolves; `FAMILY.yaml` stubs parse and their `catalog_id` matches `CATALOG_v0.1.md`.
- `test_variant_placement.py` — no directory under `variants/` or `keys/` is ever treated as a
  version by `workbench_tree.py`.
- `test_no_orphan_versions.py` — the count of version directories per family before and after the
  move is identical. This catches a partial `git mv` silently dropping one.

## Rollback

Per family, reverse the move and remove the junction. Because each family is one commit,
`git revert` is clean. The pilot is the exception worth stating: if the pilot fails its run
comparison, revert it and stop the entire phase.

## Done criteria

- All thirty-three families at their catalog paths, version names unchanged.
- Version directory counts identical before and after, per family.
- Every junction verified by SHA-256, not by existence.
- The pilot reproduces its pre-move output manifest hash.
- At least five families from Groups B and C run successfully through their **old** paths without
  modification.
