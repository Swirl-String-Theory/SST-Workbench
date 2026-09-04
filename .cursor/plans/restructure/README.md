# SST-Workbench Restructure — planning set

Planning documents for migrating the Workbench from 73 flat top-level families to a ten-domain
catalog. **Nothing in this directory moves files.** These are plans; execution happens through the
sub-plans, one at a time, each with its own rollback.

Snapshot the plan is built on: 73 top-level families, 275 version directories, 50,813 tracked
files, ~11.9 GB tracked content, measured 2026-09-03.

## Reading order

1. [RESTRUCTURE_EPIC.plan.md](RESTRUCTURE_EPIC.plan.md) — the model, the invariants, why the phases are
   ordered the way they are. Read this first; everything else assumes it.
2. [CATALOG_v0.1.md](CATALOG_v0.1.md) — the permanent ID registry. Every research family, library,
   dataset and tool with its catalog code. This outlives the migration.
3. [RESTRUCTURE_PLAN_v0.1.plan.md](RESTRUCTURE_PLAN_v0.1.plan.md) — the one-time mapping: all 73 current
   root folders to exact destinations.
4. `SP00`–`SP11` — the executable sub-plans, in dependency order.

## Sub-plans

| ID | Title | Priority | Risk |
|----|-------|----------|------|
| [SP00](SP00_freeze_and_provenance.plan.md) | Freeze and provenance | P0 | low |
| [SP01](SP01_path_resolver.plan.md) | Central path resolver | P0 | low |
| [SP02](SP02_compat_junction_layer.plan.md) | Compatibility junction layer, stage 1 | P0 | low |
| [SP03](SP03_catalog_skeleton_and_hygiene.plan.md) | Catalog skeleton and repo hygiene | P1 | low |
| [SP04](SP04_low_risk_moves.plan.md) | Low-risk moves | P1 | low |
| [SP05](SP05_clean_family_moves.plan.md) | Clean family moves | P1 | medium |
| [SP06](SP06_container_splits.plan.md) | Ambiguous container splits | P2 | medium |
| [SP07](SP07_knotplot_refactor.plan.md) | KnotPlot tool/data/campaign/result split | P2 | high |
| [SP08](SP08_catalog_metadata_and_registry.plan.md) | Catalog metadata and registry | P3 | medium |
| [SP09](SP09_version_rename_stage2.plan.md) | Version-directory rename, stage 2 | P3 | medium |
| [SP10](SP10_reproducibility_gate.plan.md) | Reproducibility gate | P3 | medium |
| [SP11](SP11_decommission.plan.md) | Decommission | P4 | high |

## Status legend

Each sub-plan carries a status line at the top:

- `PLANNED` — written, not started
- `IN PROGRESS` — partially executed; the sub-plan records where it stopped
- `DONE` — completed and verified against its done-criteria
- `BLOCKED` — waiting on a dependency or a decision, with the blocker named

All twelve were `PLANNED` at the time of writing. **SP00 is `DONE`** (see
`10_docs/migration/FREEZE.md`); the rest remain `PLANNED`.

## Hard rules that apply to every sub-plan

1. **Never delete during a move.** Moves are `git mv` or `robocopy /MOVE`. Deletion happens only
   in SP11, only after SP10 has passed.
2. **Every move gets a row in `path_map.csv`** before it happens, and a status update after.
3. **Old paths keep working** until SP11 removes the junctions. If a move breaks an old path, the
   move is wrong, not the caller.
4. **Reproducibility beats tidiness.** A structurally imperfect layout that reproduces published
   numbers wins over a clean one that does not.
