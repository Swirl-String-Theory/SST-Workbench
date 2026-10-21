# A006 RoundFolded NearUnknot — WHOLE Component Borromean Patch v0.4.2

**Development patch for the installed A006-v0.4.0_TWIST_TORUS_MATRIX + BORROMEAN v0.4.1.**

This replaces **only the method of generating the new variants**: it adds `BORROMEAN WHOLE`; it does not alter the legacy `BORROMEAN BUILD`, the original `run_all.cmd`, the desktop shortcut, RC, the original seed files, or prior outputs.

## Why a new extension?

The previous v0.4.1 decorated-link placed localized knot bundles on carriers. The user requires each **entire** component to be the round-folded 5_2 / 5_2 / 6_1 near-unknot geometry. Here, a complete source closed curve is transported onto each of the three user-supplied reference configurations with its own plane and axis. There is no splice, no carrier concatenation and no fourth ring component. This is a *geometric candidate*, not a proof of a Borromean link.

The exact two uploaded references `borromean_flat.txt` (38/34/33 points) and `borromean_balanced.txt` (38/34/33 points) are copied unchanged into `output/borromean/`. Note that `flat` means *the supplied almost-flat configuration*, not `z=0` for every bead; measured nonzero z coordinates are retained. `balanced` names the user-supplied configuration and does not constitute certified hydrodynamic equilibrium.

## Installation

Unzip as `patch_staging/A006_BORROMEAN_WHOLE_PATCH_v0.4.2/` INSIDE the existing

`C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.4.0_TWIST_TORUS_MATRIX`.

Execute in that existing project root:

```bat
py -3 patch_staging\A006_BORROMEAN_WHOLE_PATCH_v0.4.2\install_patch.py --base . --check
py -3 patch_staging\A006_BORROMEAN_WHOLE_PATCH_v0.4.2\install_patch.py --base . --apply
run_all.cmd BORROMEAN WHOLE TEST
run_all.cmd BORROMEAN WHOLE PLAN
run_all.cmd BORROMEAN WHOLE BUILD
```

`BUILD` produces 1024 beads per whole component. `BUILD FULL` produces 2048. The generator verifies the SHA-256 manifest of native 5_2 and 6_1 seeds at build time. Re-running the same build skips **byte-identical** XYZ data; conflicting outputs abort rather than being overwritten.

## Compact KnotPlot paths

All new files are in the **same flat output directory**: `output/borromean/`.

```text
load output/borromean/borromean_flat.txt
load output/borromean/borromean_balanced.txt
load output/borromean/Borromean_5_5_6_BALANCED_N1024.xyz
read output/borromean/Borromean_5_5_6_BALANCED_N1024_LOAD.kpc
read output/borromean/Borromean_5_5_6_BALANCED_N1024_TANF_OFF_PILOT.kpc
```

The `.xyz` contains *exactly three components* as three contiguous blocks of `X Y Z` rows separated by *one empty line*, no headers, no per-component paths and **no KPT loader**. The load script uses `load ...xyz`, not `load ...kpt`.

Profiles: `FLAT` follows `borromean_flat.txt`; `BALANCED` follows `borromean_balanced.txt`; `SOFT` and `TIGHT` are alternate static width/height parameterizations of the balanced 3-axis carrier reference. Each load comes with `TANF_ON_PILOT` and `TANF_OFF_PILOT` scripts using *atomic `ago`* checkpoints 0,1,8,32,128,512. Start `LOAD` or `TANF_OFF_PILOT` first.

## Qualification

The constructor tests combined-XYZ formatting, original-file hashes, fixed component count, nonlocal polygonal distances (self and intercomponent), and approximate pairwise Gauss-linking integrals. Both 1024- and 2048-bead modes pass the **static numerical thresholds** on the original v0.4.0 fixture at the **same scale of 60**.

**DO NOT promote to `STATIC_READY` / genuine Borromean:** the individual source centerline winds zero net times about its near-circle geometric center. Tubular transport does not guarantee the Milnor triple invariant or even preservation of the intended individual Alexander polynomial. The desired Borromean link requires **independent knot identification after transport and `|mu123|=1`**, as well as a deformation-history/topology gate, beyond pairwise `Lk≈0` and a pleasing appearance. These remain `UNRESOLVED` or not tested.

**KnotPlot atomic `ago` does not simulate Euler/finite-core Biot–Savart fluid dynamics.** Do not infer SST toroidal rolling from the GUI relaxer.

## Patch rollback

The original wrapper is backed up to:

`patch_backups/A006_BORROMEAN_v0.4.2/run_borromean.cmd.before`

Restore this file manually over `extensions/borromean/run_borromean.cmd` if you deliberately roll back, after saving any desired new outputs. Removing `extensions/borromean/whole/` is optional. Keep all source/old outputs.
