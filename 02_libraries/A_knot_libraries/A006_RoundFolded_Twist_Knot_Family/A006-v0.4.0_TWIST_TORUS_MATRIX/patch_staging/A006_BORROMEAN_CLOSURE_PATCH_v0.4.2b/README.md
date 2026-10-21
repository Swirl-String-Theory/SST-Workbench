# A006 Borromean WHOLE v0.4.2b — periodic seam & bead allocation patch

**Target**: the existing Windows folder

`C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.4.0_TWIST_TORUS_MATRIX`

Requires installed Borromean v0.4.1 + WHOLE v0.4.2 + XYZ-ONLY v0.4.2a.

## What is fixed

- Periodic interpolation in `ref_lookup`: ghost points on BOTH sides of the reference angular range. Eliminates the v0.4.2a clipping discontinuity near phi=0 / 2pi.
- True cyclic polygonal *arclength* resampling: last-to-first edge is included in total length, without appending a duplicate endpoint/zero-length edge. One closed *mathematical polygon* per component.
- Equal N, explicit `N0 N1 N2`, or AUTO from the **final placed** component lengths.
- Strict XYZ: ONLY numerical `x y z` rows; ONE empty line between blocks; three components in one file. Different bead counts allowed. NO component headers, NO KPC, NO KPT, NO stand-alone component files.
- Checks: polygon edge-length uniformity, seam edge, pairwise Gauss linking, 3D self/intercomponent clearance, SHA-256 provenance.
- New outputs are suffixed `_v042b.xyz`; existing v0.4.2a outputs remain untouched. No new shortcuts or RC modification.

## Install

Unzip under `patch_staging/` **within your existing A006-v0.4.0 project directory**. These commands are executed from that directory:

```bat
py -3 patch_staging\A006_BORROMEAN_CLOSURE_PATCH_v0.4.2b\install_patch.py --base . --check
py -3 patch_staging\A006_BORROMEAN_CLOSURE_PATCH_v0.4.2b\install_patch.py --base . --apply
run_all.cmd BORROMEAN WHOLE TEST
run_all.cmd BORROMEAN WHOLE PLAN
```

A second install is safely rejected. The original 4 module files are preserved under `patch_backups/A006_BORROMEAN_v0.4.2b/`.

## Build commands

```bat
rem Default, 1024/1024/1024 beads for all profiles:
run_all.cmd BORROMEAN WHOLE BUILD

rem Default, 2048/2048/2048 for all profiles:
run_all.cmd BORROMEAN WHOLE BUILD FULL

rem Explicit numbers per component: 5_2 / 5_2 / 6_1
run_all.cmd BORROMEAN WHOLE BUILD BALANCED 1024 1024 1165

rem Automatically assign TOTAL points to the three FINAL placed lengths:
run_all.cmd BORROMEAN WHOLE BUILD BALANCED AUTO 3072

rem Alternative Python direct interface (can use exact desired spacing):
py -3 extensions\borromean\whole\build_whole.py --root . --profiles BALANCED --target-spacing 0.5
```

For each profile FLAT, SOFT, BALANCED, TIGHT, explicitly choose `--profiles` when using Python. `N0 N1 N2` must each be at least 32.

## Result files

`output/borromean/Borromean_5_5_6_BALANCED_N1024_1024_1165_v042b.xyz`

or AUTO with 3072 points:

`output/borromean/Borromean_5_5_6_BALANCED_N1087_1007_978_v042b.xyz`

Reports are placed beside the geometry with `_REPORT.json`. Only ONE geometry XYZ file per selected profile. Each has three numeric blocks separated by exactly one empty row. No component identifiers. No duplicated closing vertex.

## KnotPlot

Load the numeric `.xyz` directly in your existing GUI using the current A006 working folder. No LOAD scripts are generated. After import, **check with KnotPlot `close` command** whether all 3 components are marked closed. If the ASCII reader opens them, the manual command `close all` exists; this changes the KnotPlot runtime component flags, not the original XYZ. Then inspect via `information`, `length`, `safe`. Any successful KnotPlot closure/roundtrip still requires runtime verification.

## Bead length facts

Using v0.4.0 raw sources at N2048:
- native `5_2`: polygon length 850.987 KnotPlot units;
- native `6_1`: polygon length 968.210 KnotPlot units;
- native ratio L(6_1)/L(5_2) = approximately 1.13775.

`N5=1024 -> N6~1165` matches source bead spacing, **but is not guaranteed to match the new Borromean placed lengths**. The positioning/reference frames change lengths. `AUTO` is recommended if equal final bead spacing is desired, e.g. BALANCED 3072 points gives `1087,1007,978` in the static test.

`Length in short direction = 5.654867` is a separate KnotPlot `length` display value, as documented in the KnotPlot manual. This is not the individual 5_2/6_1 length or a safe bead spacing by itself.

## Scientific limitations

- `STATIC_CANDIDATE`: It is NOT independently certified that each whole-transported component retains its intended knot type. Pairwise linking near zero does NOT prove a Borromean triple linkage.
- The Milnor invariant, isotopy of whole-tube transport, KnotPlot closed flag, KnotPlot `ago` relaxation and Euler/finite-core dynamics remain UNRESOLVED / NOT RUN.
- This patch fixes polygon interpolation and bead counts; it cannot set open/closed flags in KnotPlot's ASCII loader via additional numeric lines without risking zero-length edges.

## Sources

- Scharein, R. G., *KnotPlot Manual*, https://knotplot.com/manual/commands.html (load, coords, close all).
- Scharein, R. G., *New KnotPlot Commands* (2017), https://knotplot.com/man/ (independent length output including `Length in short direction`).
