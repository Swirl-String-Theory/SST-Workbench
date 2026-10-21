# A006 v0.4.3 — Selection / Mirror / Resolution Matrix (additive patch)

Target: **existing A006-v0.4.0_TWIST_TORUS_MATRIX**, already patched to v0.4.2d.
No new project folder or shortcut. Old `BASIC`, `SMALL`, `MEDIUM`, `FULL`,
`BORROMEAN` commands, RC settings, source seeds and outputs remain unchanged.

## Installation (from the existing A006 root)

Unpack archive at `patch_staging/A006_SELECT_v0.4.3_PATCH/`.

```bat
py -3 patch_staging\A006_SELECT_v0.4.3_PATCH\install_patch.py --base . --check
py -3 patch_staging\A006_SELECT_v0.4.3_PATCH\install_patch.py --base . --apply
run_all.cmd SELECT --knots=5_2,6_1 --links=NONE --minN=256 --maxN=512 --maxIteration=1000 --checkpointsEvery=500 --mirrored=BOTH --plan
```

## All classes and mirrors

```bat
run_all.cmd --knots=ALL --links=ALL minN=256 --maxN=2048 --maxIteration=8000 --checkpointsEvery=500 --mirrored=BOTH --tanf=OFF --plan
run_all.cmd --knots=ALL --links=ALL minN=256 --maxN=2048 --maxIteration=8000 --checkpointsEvery=500 --mirrored=BOTH --tanf=OFF --prepare
run_all.cmd --knots=ALL --links=ALL minN=256 --maxN=2048 --maxIteration=8000 --checkpointsEvery=500 --mirrored=BOTH --tanf=OFF --execute
```

Without `--plan`, `--prepare`, or `--analyze`, the command attempts execution. It *fails closed* if KnotPlot is not locally preflight-qualified. First run `run_all.cmd PREFLIGHT` and set `KNOTPLOT_EXE` or `config/knotplot_exe.txt`.

Select a subset, for example:

```bat
run_all.cmd --knots=3_1,4_1,5_2,6_1,11_2 --links=6_6_5 --linkProfiles=BALANCED --minN=256 --maxN=1024 --maxIteration=8000 --checkpointsEvery=500 --mirrored=BOTH --plan
```

Aliases `11_1` => `11a367` (torus) and `11_2` => `11a247` (twist). Knot types are the 13 distinct v0.4.0 entries, including both 11-crossing types. `--linkProfiles=ALL` means `FLAT,SOFT,BALANCED,TIGHT` for both `5_5_6` and `6_6_5`. `--tanf=OFF` is the default. You can choose `ON` or `BOTH`, but `tanf` has a documented implementation bug.

N for knots = **exact** beads in the knot. N for Borromean links = **minimum beads among the three components**, with remaining counts proportional to their placed arclengths. `--minN=256 --maxN=2048` selects powers of two. Use `--beads=256,384,768` for custom exact resolutions.

`--mirrored=BOTH` runs original and full 3-D reflection `(x,y,z) -> (-x,y,z)`. The mirror is *not* an inverse parameter ordering or a camera rotation. Mirror geometries preserve edge lengths. The reference table at https://david.fremlin.de/knots/table.htm classifies known topological knot symmetries; the numerical mirror comparison does **not** determine amphichirality.

## Output contracts

- Knot seeds, generated `.kpt`/`.xyz` and scripts are **new**, exclusively under `output/selection_v043`.
- Combined Borromean source and mirrored `xyz`: exactly **three numeric XYZ blocks with two single blank separators, no labels**. No standalone `*_LOAD.kpc`, no multicomp `.kpt`.
- Each automated campaign has one `campaign.kpc`, which **internally** loads that strict XYZ when running KnotPlot. Do not mistake it for the eliminated `*_LOAD.kpc` files.
- Native KnotPlot checkpoint `coords` output may include `Component 0:` headers. These are kept in the runtime checkpoint directory, separate from the **strict** geometry import files.
- KnotPlot `ago n` is atomic. At 8000/500: early checkpoints `0,1,8,32,128,512` plus `500,1000,...,8000` (22 unique checkpoints).
- KnotPlot `data` writes `/I,/N,/l,/g,/s` to `native.csv`, after `length`, `rog`, `safe` have actually run.
- Old outputs are never overwritten. Missing Borromean source profiles are generated in private staging `output/selection_v043/_staging`, not in legacy `output/borromean`.
- Runs acquire `DONE.json` only after all checkpoints and CSV rows pass structural validation. Interrupted runs remain visible and are not silently overwritten. Reuse is restricted to the exact geometry + mirrored status + TANF settings + checkpoint schedule.

## Analysis

```bat
run_all.cmd --analyze
```

Produces `output/selection_v043/symmetry_geometry.csv` (static mirror-pair measurements) and `analysis/metrics_long.csv`, `mirror_comparison.csv`, `resolution_comparison.csv`, `AUDIT.json`, and optional charts **only from verified runtime data**.

No evidence of Euler-vortex rolling or true Borromean Milnor triple linking is supplied by this patch. Reduced-resolution polylines and whole-component link compositions remain STATIC_CANDIDATE until topology-preservation gates pass. Existing KnotPlot GUI default scale parameters are not changed.
