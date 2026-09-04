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
   **A-falsifier IDs A001–A042 are frozen to the chronological table (2026-09-04).**
3. [RESTRUCTURE_PLAN_v0.1.plan.md](RESTRUCTURE_PLAN_v0.1.plan.md) — the one-time mapping: all 73 current
   root folders to exact destinations.
4. [SST_WORKBENCH_RESTRUCTURE_MAP_v0.1.json](SST_WORKBENCH_RESTRUCTURE_MAP_v0.1.json) — machine-readable
   merge of CATALOG + PLAN + `path_map.csv` (version targets remapped from the legacy draft).
   Where IDs disagree, **CATALOG wins**; where moves disagree, **`path_map.csv` wins**.
5. `SP00`–`SP11` — the executable sub-plans, in dependency order.

## Sub-plans

| ID | Title | Status | Progress | Priority | Risk |
|----|-------|--------|----------|----------|------|
| [SP00](SP00_freeze_and_provenance.plan.md) | Freeze and provenance | `DONE` | 8/8 | P0 | low |
| [SP01](SP01_path_resolver.plan.md) | Central path resolver | `DONE` | 10/10 | P0 | low |
| [SP02](SP02_compat_junction_layer.plan.md) | Compatibility junction layer, stage 1 | `DONE` | 6/6 | P0 | low |
| [SP03](SP03_catalog_skeleton_and_hygiene.plan.md) | Catalog skeleton and repo hygiene | `DONE` | 7/7 | P1 | low |
| [SP04](SP04_low_risk_moves.plan.md) | Low-risk moves | `DONE` | 5/5 | P1 | low |
| [SP05](SP05_clean_family_moves.plan.md) | Clean family moves | `PLANNED` | 0/6 | P1 | medium |
| [SP06](SP06_container_splits.plan.md) | Ambiguous container splits | `PLANNED` | 0/5 | P2 | medium |
| [SP07](SP07_knotplot_refactor.plan.md) | KnotPlot tool/data/campaign/result split | `PLANNED` | 0/5 | P2 | high |
| [SP08](SP08_catalog_metadata_and_registry.plan.md) | Catalog metadata and registry | `PLANNED` | 0/5 | P3 | medium |
| [SP09](SP09_version_rename_stage2.plan.md) | Version-directory rename, stage 2 | `PLANNED` | 0/5 | P3 | medium |
| [SP10](SP10_reproducibility_gate.plan.md) | Reproducibility gate | `PLANNED` | 0/5 | P3 | medium |
| [SP11](SP11_decommission.plan.md) | Soft-retire (`DELETE/`) + decommission | `PLANNED` | 0/6 | P4 | high |

Also tracked: [RESTRUCTURE_EPIC](RESTRUCTURE_EPIC.plan.md) (5/12 planning done) ·
[RESTRUCTURE_PLAN](RESTRUCTURE_PLAN_v0.1.plan.md) (5/11 mapping freeze done).
Each file has a **Todos** section (checked = done) and YAML frontmatter todos for Cursor.

**Resume here:** SP01 path resolver (SP00 is closed).


## Status legend

Each sub-plan carries a status line at the top:

- `PLANNED` — written, not started
- `IN PROGRESS` — partially executed; the sub-plan records where it stopped
- `DONE` — completed and verified against its done-criteria
- `BLOCKED` — waiting on a dependency or a decision, with the blocker named

All twelve were `PLANNED` at the time of writing. **SP00 is `DONE`** (see
`10_docs/migration/FREEZE.md`); the rest remain `PLANNED`. Open each file’s **Todos**
section to see what is already checked off versus what remains.

## Hard rules that apply to every sub-plan

1. **Never delete content.** Moves are `git mv`. Anything formerly slated for deletion goes to
   `DELETE/<original/relative/path>` (still via `git mv`). SP11 soft-retires only after SP10.
2. **Every move gets a row in `path_map.csv`** before it happens, and a status update after.
3. **Old paths keep working** until SP11 removes the junctions. If a move breaks an old path, the
   move is wrong, not the caller.
4. **Reproducibility beats tidiness.** A structurally imperfect layout that reproduces published
   numbers wins over a clean one that does not.
