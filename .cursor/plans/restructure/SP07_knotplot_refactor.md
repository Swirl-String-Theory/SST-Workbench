# SP07 — KnotPlot tool / data / campaign / result split

Status: `PLANNED` · Priority: P2 · Risk: **high** · Depends on: SP05

The highest-risk sub-plan. `KnotPlot/` is ~12.4 GB, 12,979 tracked files, and roughly 1,458 files
elsewhere in the repo reference it by name. It is also the only root where four conceptually
different things share one directory.

```text
generator/tool  !=  input geometry  !=  campaign  !=  campaign result
```

All four are currently under `KnotPlot/`, which is why `latest`, `outputs` and `knots` all mean
something different depending on which subtree you are in.

## Why this is separate from SP06

Three reasons, any one of which is sufficient:

1. **Scale.** `knots/` alone is ~7.8 GB with 8,285 tracked files. A failed move here is not a quick
   revert.
2. **Reference density.** `..\..\KnotPlot\knots\final` is the default dataset for 40+ packs. This
   junction is the one that matters most in the entire migration.
3. **The tool is not in the repo.** `KnotPlot.lnk` points at an external KnotPlot executable. The
   tool directory holds drivers and `.kps` scripts, not the program. Moving it changes what the
   `.lnk` and the `.kps` relative references resolve against.

## Target split

| From | To | Kind | Size |
|------|----|------|-----:|
| `KnotPlot/*.py`, `*.kps`, `*.lnk`, `run_build*.cmd`, `knotplot_knots_data.js` | `04_tools/A_geometry/A001_knotplot/` | tool | small |
| `KnotPlot/ridgerunner/` excluding `out/` | `04_tools/A_geometry/A002_ridgerunner/` | tool | ~50 MB |
| `KnotPlot/knots/` | `03_data/A_knots/A001_knotplot_relaxed/` | data | ~7.8 GB |
| `KnotPlot/Knots_FourierSeries/` | `03_data/A_knots/A002_knotplot_fourier_series/` | data | ~0.7 MB |
| `KnotPlot/qhp/`, `qhp_6p3/`, `qhp_extended/` | `03_data/A_knots/A003_knotplot_qhp/` | data | ~29 MB |
| `KnotPlot/ridgerunner/out/` | `03_data/D_generated/D005_knotplot_campaign_outputs/` | output | ~3.9 GB |
| `KnotPlot/Trefoil_Balance_Point_Campaign_v*` (6) | `01_research/E_pipelines/E004_knotplot_trefoil_balance_point/` | campaign | ~413 MB |
| `KnotPlot/KnotPlot_3p1_Trefoil_Seed_Campaign_v*` (2) | `.../E005_knotplot_trefoil_seed/` | campaign | ~133 MB |
| `KnotPlot/KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v*` (7) | `.../E006_knotplot_multidynamics_relaxation_matrix/` | campaign | ~85 MB |
| `KnotPlot/KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v*` (3) | `.../E007_knotplot_dynamics_parameter_atlas/` | campaign | ~188 MB |
| `KnotPlot/KnotPlot_3p1_MissingParameter_Command_Certification_v0.2.0` | `.../E008_knotplot_command_certification/` | campaign | ~2 MB |
| `KnotPlot/KnotPlot_MultiTopology_QHP_Sweep_v0.3.2` | `.../E009_knotplot_multitopology_qhp_sweep/` | campaign | ~99 MB |
| `KnotPlot/*_outputs.zip` (17) + `.sha256` | `09_archive/restore/KnotPlot/` | archive | — |

## Execution order

Reverse of risk. Each step is its own commit and its own verification.

1. **Archive zips** (17 files). Zero references. Warm-up.
2. **`qhp*/`** (~29 MB). Few references, mostly from `SST_QHP_Stability_Landscape`, already split in
   SP06.
3. **`Knots_FourierSeries/`** (~0.7 MB). Referenced by `SST_Fourier_vs_Ideal_Blind_Falsifier` via
   `SST_FVI_FSERIES`, which is already an override-able variable — the easiest real test of the
   resolver.
4. **Campaign directories** (E004–E009, ~920 MB). Self-contained; their outputs currently live
   inside them and travel along.
5. **`ridgerunner/out/`** (~3.9 GB). Mostly gitignored (`KnotPlot/ridgerunner/out/` is in
   `.gitignore`, only 67 files tracked under `ridgerunner/` in total), so this is a filesystem move
   with almost no index change. Big, but cheap.
6. **`ridgerunner/`** remainder → tool.
7. **Tool scripts at the `KnotPlot/` root.**
8. **`knots/`** (~7.8 GB, 8,285 tracked files). **Last, alone, its own commit.**

## The `knots/final` junction

This is the single most important junction in the migration. Before moving `knots/`:

- Confirm SP02's junction machinery has worked correctly for at least ten prior moves.
- Confirm `.git/info/exclude` handling has been verified, not assumed — 8,285 tracked files
  double-staged would be a painful recovery.
- Have `SST_KNOT_DATASET` pointing at the new location and at least three packs converted to use
  it, so there is a non-junction path that also works.

After moving, both of these must resolve to the same file with the same SHA-256:

```text
KnotPlot\knots\final\<known file>                                    (through the junction)
03_data\A_knots\A001_knotplot_relaxed\final\<known file>             (direct)
```

## Circular references to break first

`KnotPlot/KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0/run_80_sst_v048_preflight.cmd`
sets `SST_V048_DIR` to an absolute path inside `SST_Trefoil_Lobe_Orientation_Blind_Falsifier/`, and
that pack's run scripts set `SST_ATLAS_ROOT` to an absolute path back into KnotPlot. After SP06
moves one side and SP07 moves the other, two junction layers would be covering each other.

Convert both to `resolve_family("A021")` and `resolve_family("E007")` **before** step 4. This is
listed in SP06 §4 as well; whichever phase reaches it first does it.

## Tool scripts that will need attention

These live at the `KnotPlot/` root and resolve paths relative to themselves:

- `build_knotplot_knots_data.py` — builds `knotplot_knots_data.js` from exports; also consumed by
  `GUI/vortexring-lab/`, which SP06 moved to `05_apps/A003_vortexlab/`.
- `ideal_resolver.py`, `gilbert_reader.py`, `knotplot_txt_to_vect.py`,
  `resample_closed_knot_txt.py`
- `ridgerunner/gilbert_ab_to_xyz.py:27` — `BUNDLE.parents[1]` assumes the workbench root is two
  levels up. Becomes four levels up after the move; convert to the resolver rather than adjusting
  the count.
- `ridgerunner/test_run_ideal_knot.py:55,317` and `test_recover_ladder_coarse.py:38` — absolute
  paths into the workbench. Convert.
- `test_sst_gilbert_usability.py:28` at the repo root — `ROOT / "KnotPlot" / "ridgerunner"`.
  Convert; it is part of the documented baseline suite.

## Tests to write

- `test_knotplot_split.py` — every child of the old `KnotPlot/` is accounted for in exactly one
  destination; nothing is duplicated; the tracked file count before equals the sum after.
- `test_knot_dataset_resolution.py` — `SST_KNOT_DATASET` resolves; the same known knot file has an
  identical SHA-256 through the junction and through the direct path; a pack using the old
  hardcoded `..\..\KnotPlot\knots\final` still loads it.
- `test_campaign_isolation.py` — no campaign directory contains input geometry, and no dataset
  directory contains a campaign definition. This is the structural assertion the whole sub-plan
  exists to establish.
- Update `scripts/test_workbench_tree.py`, which asserts on `KnotPlot/knots/` and
  `Campaign_v0.1.0` literals.

## Rollback

Per step, and each step is small enough to revert except step 8. For `knots/`:

- Do not attempt a partial revert. Either the move completed and verified, or `git mv` it back
  whole.
- Keep `checksums.sha256` from SP00 available throughout. It is the only way to prove 8,285 files
  arrived intact.
- Budget for the move to take a long time and do not interrupt it. An interrupted 7.8 GB move
  leaves a half-populated target that is hard to distinguish from a completed one.

## Done criteria

- Twelve destinations populated; the old `KnotPlot/` root exists only as a real directory holding
  junctions to each destination.
- `test_campaign_isolation.py` passes — the four kinds of thing are actually separated.
- A knot file loads identically through both paths, verified by hash.
- At least five of the 40+ packs that default to `..\..\KnotPlot\knots\final` run unmodified.
- Tracked file count before equals sum after: 12,979.
