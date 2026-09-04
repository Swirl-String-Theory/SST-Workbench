# SST KnotPlot QHP Sweep Generator v0.1.1

Creates controlled Q/H/P geometry sweeps from relaxed KnotPlot/Ridgerunner XYZ centerlines and writes metadata directly consumable by **SST QHP Stability Landscape Blind Falsifier**.

## Default paths

Input:

```text
..\..\KnotPlot\knots\final
```

Output:

```text
..\..\KnotPlot\qhp
```

Run:

```bat
run_all.cmd
```

Focus first on the near-balance **knot_6.3** seed:

```bat
run_setup.cmd
run_focus_6p3.cmd
```

## Q/H/P definitions

The seed is first uniformly resampled in arclength. The zero point `(q,h,p)=(0,0,0)` is exactly the resampled relaxed seed.

- **Q — normal-plane breathing:** centroid-radial displacement with tangential and rigid components removed.
- **H — axial flatten/elongation:** traceless PCA-axis deformation along the smallest-variance principal axis, again stripped of tangential/rigid components.
- **P — phase/shear:** an arclength-harmonic azimuthal displacement about the PCA axis. The harmonic prevents P from degenerating into a rigid rotation.

Each basis has RMS displacement exactly equal to the seed radius of gyration `Rg`. Therefore `q=0.05` means a 5% `Rg` RMS displacement along the Q basis, and similarly for H and P.

No KnotPlot force/energy parameter is used as a physics claim. These are **controlled centerline perturbations** around a KnotPlot/Ridgerunner seed. KnotPlot can be used to inspect them, but the downstream Euler/finite-core falsifier provides the physical stability verdict.

## BASIC

`config/basic.json` uses amplitudes `[-0.05,-0.02,0,+0.02,+0.05]` and the three separate axes. Because the common zero point is shared, this creates 13 unique geometries per seed.

## EXTENDED

`config/extended.json` adds `+-0.10`, uses 384 arclength samples and still stays on the three separate axes.

## FULL GRID

Only after axis sweeps identify an interesting basin:

```bat
run_full_grid.cmd
```

This produces a 5x5x5 local QHP cube per seed.

## Seed identity integrity

Each source seed is its own QHP manifold. The metadata `family` is therefore a unique source identity such as `knot_6.3`, `link_6.3.1`, or `torus_2.3`. The shorter numeric `topology_class` (for example `6.3`) is retained only as descriptive metadata and is never used to merge different seeds.

The generator refuses duplicate output paths before writing. `run_*.cmd` also uses guarded `--clean-output`, which only replaces an empty directory or a directory already carrying a recognized QHP generator summary.

**Do not use v0.1.0 outputs when multiple seed files shared the same numeric class** (for example `knot_6.3` and `link_6.3.*`); those paths could collide. Regenerate them with v0.1.1.

## Geometry safety gates

Each output records `separation_ratio`, `ds_cv`, and `geometry_ok`. A rejected geometry is still written for auditability but can be excluded by the downstream campaign.

## Output

```text
KnotPlot/qhp/
  qhp_metadata.csv
  seed_manifest.csv
  QHP_SWEEP_SUMMARY.json
  knot_6.3/
    knot_6p3_qm0p05_h0_p0.txt
    knot_6p3_q0_h0_p0.txt
    knot_6p3_q0p05_h0_p0.txt
  link_6.3.1/
    link_6p3p1_q0_h0_p0.txt
    ...
```

`qhp_metadata.csv` contains explicit signed numeric `q,h,p` values; no filename inference is required downstream.
