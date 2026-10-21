# A006 RoundFolded NearUnknot v0.4.0 — Borromean in-place patch v0.4.1

**This is a PATCH for the existing v0.4.0 directory, not a separate v0.4.1 library.**

Install target (do not rename or move the project):

`C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.4.0_TWIST_TORUS_MATRIX`

Unpack patch ZIP inside the project under `patch_staging` to get
`patch_staging\A006_BORROMEAN_PATCH_v0.4.1\install_patch.py`.

From **the existing v0.4.0 root**:

```bat
py -3 patch_staging\A006_BORROMEAN_PATCH_v0.4.1\install_patch.py --base . --check
py -3 patch_staging\A006_BORROMEAN_PATCH_v0.4.1\install_patch.py --base . --apply
run_all.cmd BORROMEAN TEST
run_all.cmd BORROMEAN PLAN
run_all.cmd BORROMEAN BUILD
run_all.cmd BORROMEAN PILOT
```

`BORROMEAN BUILD FULL` requests experimental 2048 bead geometry. Only start a KnotPlot script if
all static checks have `PASS`, and only use one generated KPC at a time. Example:

```
read output/borromean_55261/Borromean_5_2_5_2_6_1_SOFT_N1024/Borromean_5_2_5_2_6_1_SOFT_N1024_TANF_OFF_PILOT.kpc
```

**In-place design:** Existing `run_all.cmd` gets a guarded BORROMEAN branch.
Everything else is NEW under `extensions/borromean/` and `output/borromean_55261/`.
Original `run_all.cmd` is backed up under `patch_backups/`.

Original shortcuts, KnotPlot RC, existing scripts, BASE modes BASIC/SMALL/MEDIUM/FULL,
existing outputs, and original `output/seeds` remain unchanged. Re-applying the patch
is rejected. The installer refuses unknown or modified native seeds.

## Scientific scope

Three-component `5_2 + 5_2 + 6_1` **Borromean-decorated link candidate**, with
reference braid `(sigma_1 sigma_2^-1)^3`, grafted using original v0.4.0 KPT data.
Components are not unknotted; therefore this is NOT a strictly Brunnian link.
Pairwise Gauss linking ~ 0 and static filament clearance are necessary checks, but
**not sufficient** to certify individual knot types or nonzero Milnor triple invariant.
Independent component Alexander/Jones and triple-link certification are still UNRESOLVED.

KnotPlot `ago` is a geometric force relaxation, NOT finite-core Euler/Biot-Savart dynamics.
`tanforce ON` is a separate bug-sensitive numerical perturbation; start with OFF.

Tested against the actual source v0.4.0 ZIP in an isolated Linux filesystem fixture;
not executed in KnotPlot on user's Windows workstation. No existing files on PC modified.
