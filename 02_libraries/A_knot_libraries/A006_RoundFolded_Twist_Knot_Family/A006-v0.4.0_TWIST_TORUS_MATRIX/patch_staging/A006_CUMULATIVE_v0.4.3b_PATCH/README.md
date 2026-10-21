# A006 RoundFolded v0.4.3b — cumulative Selection, BeadLimit & Closure Orientation

**INSTALL SOURCE: v0.4.2d (with v0.4.0 seeds). Do NOT install v0.4.3 or v0.4.3a first.**

This cumulative patch contains all three updates in one installation:

- v0.4.3: selectable knots `3_1` through `11_2` (`11a247`), torus `11_1` (`11a367`), links `5_5_6` and `6_6_5`, arbitrary basic bead range, mirrors, atomic `ago` and CSV analysis.
- v0.4.3a: `go beadlimit` automatically chosen from *actual total beads* in the loaded geometry, before `ago`.
- v0.4.3b: whole-component Borromean clasp placement with `LEGACY`, `CENTER`, or `MANUAL`.

## Install without creating a new A006 project or shortcuts

Extract this ZIP within `patch_staging` in your existing
`C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.4.0_TWIST_TORUS_MATRIX` folder.

```bat
py -3 patch_staging\A006_CUMULATIVE_v0.4.3b_PATCH\install_patch.py --base . --check
py -3 patch_staging\A006_CUMULATIVE_v0.4.3b_PATCH\install_patch.py --base . --apply
py -3 tools\selection_v043b.py --selftest
```

The installer backs up `run_all.cmd` and adds a dispatcher, leaving legacy `BASIC/SMALL/MEDIUM/FULL` and `BORROMEAN WHOLE` intact. No `knotplotrc`, shortcut, sources or existing outputs are replaced. The installer refuses double application and refuses any pre-existing v0.4.3 dispatcher; use this cumulative patch **directly on v0.4.2d**.

## Full campaign (planning first)

```bat
run_all.cmd --knots=ALL --links=ALL --minN=256 --maxN=2048 --maxIteration=8000 --checkpointsEvery=500 --mirrored=BOTH --closurePolicy=CENTER --plan
```

Prepare geometry and atomic scripts **without** starting KnotPlot:

```bat
run_all.cmd --knots=ALL --links=ALL --minN=256 --maxN=2048 --maxIteration=8000 --checkpointsEvery=500 --mirrored=BOTH --closurePolicy=CENTER --prepare
```

Execute only after `run_all.cmd PREFLIGHT` passes locally and you have reviewed the plan:

```bat
run_all.cmd --knots=ALL --links=ALL --minN=256 --maxN=2048 --maxIteration=8000 --checkpointsEvery=500 --mirrored=BOTH --closurePolicy=CENTER --execute
```

Analysis (does not invent runtime data):

```bat
run_all.cmd --analyze
```

## Targeted Borromean orientation comparison

The exact existing v0.4.2d geometry is the `LEGACY` control:

```bat
run_all.cmd --knots=NONE --links=5_5_6 --linkProfiles=BALANCED --minN=256 --maxN=512 --mirrored=BOTH --closurePolicy=LEGACY --prepare
```

`CENTER` uses a geometric maximum-smoothed-curvature *proxy* for the clasp. It tests 0° or 180° **only for components labelled `6_1`**, leaving `5_2` alone, and accepts the closest-to-centre candidate that passes numerical intercomponent clearance and pairwise linking. For `5_5_6 BALANCED MIN256`, the tested choice is `0,0,180`; for `6_6_5 BALANCED MIN256`, `180,180,0`.

```bat
run_all.cmd --knots=NONE --links=5_5_6 --linkProfiles=BALANCED --minN=256 --maxN=512 --mirrored=BOTH --closurePolicy=CENTER --prepare
```

Manual orientation: **three in-plane angles, degrees**, applied to the *whole placed component* around its own fitted ring normal. Not a parametric reindex, not a tilt to a new plane, and not a vortex cross-sectional material roll.

```bat
run_all.cmd --knots=NONE --links=5_5_6 --linkProfiles=BALANCED --minN=256 --maxN=512 --mirrored=BOTH --closurePolicy=MANUAL --closureAngles=0,0,180 --prepare
```

The original source `5_2/6_1` seeds remain unmodified. New generated output is under `output/selection_v043b/` and geometry names include their orientation policy, so manual, legacy and center variants cannot overwrite one another. Every *link* geometry file is ONE **numeric-only** XYZ file, with **exactly one blank line between the three component blocks**, no `Component` headers, no `_LOAD.kpc` and no multicomponent `.kpt`.

An internal `campaign.kpc` (which calls `load`, `ago`, data and coords) is generated for **automated headless execution**, not for loading geometry in your GUI. Direct GUI load is simply `load output/selection_v043b/geometry/<name>.xyz`.

## Validation status

- Synthetic tests + actual A006 v0.4.2d `5_5_6`/`6_6_5` geometry tests performed in the packaging environment.
- `CENTER` uses **only an imperfect curvature-based landmark heuristic**; this does not prove the local crossing is exactly where anticipated by eye.
- Even though each isolated knotted component undergoes an exact rigid rotation, moving one component relative to others can change **the entire link type**. Pairwise Gauss linking near zero does NOT establish Borromean `mu123`.
- KnotPlot's relaxation is artificial MD, not Euler or finite-core Biot–Savart. All physical results, triple linking and complete knot/link isotopy qualification remain **UNRESOLVED**.
- `GO`/`AGO` execution on your Windows system remains **NOT EXECUTED**; use `--prepare` first.

## Notes

- `--minN/--maxN` on links counts *beads of the shortest placed component*, not the total beads of the link.
- `--mirrored=OFF|ON|BOTH` generates a 3D reflection; symmetry comparison is not a topological symmetry-group certification.
- `--tanf=OFF|ON|BOTH` defaults to OFF because KnotPlot documents a bug in this force term.
- `--linkScale=0.80` is the default for links; other values may change the relationship between numerical `close` distance and physical scale.
- The estimated bead limit is `4000,8000,16000,...` strictly greater than the sum of loaded beads when that sum exceeds 3000.
