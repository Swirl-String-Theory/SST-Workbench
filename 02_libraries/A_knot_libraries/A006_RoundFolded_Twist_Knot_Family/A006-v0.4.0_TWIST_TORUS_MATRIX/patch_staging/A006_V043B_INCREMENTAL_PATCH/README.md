# A006 v0.4.3b INCREMENTAL Upgrade (from v0.4.3 or v0.4.3a)

## Why this patch exists

The prior **cumulative** v0.4.3b patch only targets an A006 v0.4.2d installation with **no** selection dispatcher installed. On a v0.4.3 or v0.4.3a installation, it correctly refuses with `Selection patch installed already`.

This new **incremental** patch is the correct path. **Do not delete or revert your existing v0.4.3/v0.4.3a files.**

## Target

Run these commands from the existing folder:

`C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.4.0_TWIST_TORUS_MATRIX`

Extract the ZIP so `patch_staging\A006_V043B_INCREMENTAL_PATCH\install_patch.py` exists, then:

```bat
py -3 patch_staging\A006_V043B_INCREMENTAL_PATCH\install_patch.py --base . --check
py -3 patch_staging\A006_V043B_INCREMENTAL_PATCH\install_patch.py --base . --apply
py -3 tools\selection_v043b.py --selftest
```

This patch keeps the **existing** `tools\selection_v043.py` and `tools\analysis_v043.py` unchanged. Only the existing selector call inside `run_all.cmd` is redirected from `selection_v043.py` to `selection_v043b.py`. All earlier `run_all.cmd` branches, original geometries, original runs, and `knotplotrc` remain intact.

New modules:

- `tools\selection_v043b.py` (selection + beadlimit + closure orientation)
- `tools\orientation_v043b.py` (rigid per-component orientation)
- `tools\analysis_v043b.py` (reads only `output\selection_v043b`)

New output root: `output\selection_v043b\`. The original `output\selection_v043` stays in place, and is not treated as certified equivalent or copied over.

## Test without running KnotPlot

```bat
run_all.cmd --knots=5_2,6_1 --links=NONE --minN=256 --maxN=512 --maxIteration=1000 --checkpointsEvery=500 --mirrored=BOTH --plan
run_all.cmd --knots=NONE --links=5_5_6,6_6_5 --linkProfiles=BALANCED --minN=256 --maxN=256 --maxIteration=32 --checkpointsEvery=16 --mirrored=OFF --closurePolicy=CENTER --prepare
```

`--prepare` generates geometries and *internal* atomic KnotPlot campaign scripts without running KnotPlot. Multi-component geometry stays in **one headerless XYZ** with exactly one blank line between the three component blocks. No standalone `LOAD.kpc` is created for links. `--execute` requires the separate KnotPlot Windows/headless preflight and has not been run here.

## Operational notes

- Supported upgrade: **v0.4.3** or **v0.4.3a**, not unpatched v0.4.2d. Use the cumulative patch only for a clean unpatched v0.4.2d.
- The installed patch checks `run_all.cmd` for the precise v0.4.3 selector line and refuses unknown structures.
- Existing results are retained and no original source seeds are rewritten.
- Repeated `--apply` is refused; subsequent `--check` returns `ALREADY_INSTALLED`.
- A backup and checksum receipt are written under `patch_backups\A006_v0.4.3b_INCREMENTAL`.
- Optional guarded rollback: `py -3 patch_staging\A006_V043B_INCREMENTAL_PATCH\install_patch.py --base . --rollback`. Rollback refuses if files changed after patch installation.
- `--closurePolicy=CENTER` uses a **geometric proxy**, not independent certification of the Borromean topology. Pairwise Gauss linking near zero does not establish Milnor triple linking. KnotPlot MD is not Euler/PKLSA dynamics.
