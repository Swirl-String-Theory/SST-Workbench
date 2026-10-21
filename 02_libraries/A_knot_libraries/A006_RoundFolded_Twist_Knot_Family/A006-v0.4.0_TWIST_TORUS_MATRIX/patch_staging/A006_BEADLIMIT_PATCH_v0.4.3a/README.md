# A006 RoundFolded v0.4.3a — KnotPlot beadlimit hotfix

This is an **in-place, fail-closed hotfix on top of A006 v0.4.3**. It does not install v0.4.3 or alter `run_all.cmd`, shortcuts, `knotplotrc`, source seeds, source geometry, or prior KnotPlot output.

## Problem reproduced on supplied A006 v0.4.2d source

`Output/borromean/Borromean_5_5_6_FLAT_MIN1024_S0800_v042c.xyz` has three components with **1215 + 1101 + 1024 = 3340** beads. KnotPlot's default relaxation limit reported by the user is 3000. An ordinary `ago ...` fails unless the limit is raised.

## Fix

For each new campaign script the runner obtains `n_actual` from its geometry report (for a link this is the count across **all three** blocks), and inserts **after `load` but before any `ago`**:

- Total 1–3000: no extra command (old KPC and protocol hashes preserved).
- Total 3001–3999: `go beadlimit 4000`.
- Total 4000–7999: `go beadlimit 8000` (strictly higher than bead count).
- Total 8000–15999: `go beadlimit 16000`.
- And so forth (powers of two starting from 4000).

Example generated KPC:

```text
load output/selection_v043/geometry/LINK_5_5_6_FLAT_N1024_ORIG.xyz
go beadlimit 4000
information
length
safe
...
ago 1
...
```

No new KPC LOAD-only script is produced; this adjustment is solely inside the v0.4.3 **dynamics campaign**. The original headerless three-block XYZ import format is unchanged.

## Installation

Target project root on user's PC:

`C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.4.0_TWIST_TORUS_MATRIX`

Extract the ZIP so that the installer is under
`patch_staging\A006_BEADLIMIT_PATCH_v0.4.3a\install_patch.py`.

Run **from the project root**:

```bat
py -3 patch_staging\A006_BEADLIMIT_PATCH_v0.4.3a\install_patch.py --base . --check
py -3 patch_staging\A006_BEADLIMIT_PATCH_v0.4.3a\install_patch.py --base . --apply
py -3 tools\selection_v043.py --selftest
```

A SHA-256 check rejects unexpected modifications of the v0.4.3 selector. A backup is written to `patch_backups/selection_v043a_beadlimit/` before replacement. Re-applying is blocked.

Generate fresh campaigns:

```bat
run_all.cmd --knots=NONE --links=5_5_6 --linkProfiles=FLAT --minN=1024 --maxN=2048 --maxIteration=8000 --checkpointsEvery=500 --mirrored=BOTH --prepare
```

Review new `output/selection_v043/runs/**/campaign.kpc` files to verify `go beadlimit` appears after `load`, before `ago`. For *actual headless execution*, follow the existing v0.4.3 `PREFLIGHT` protocol and use `--execute` rather than `--prepare`.

**If you manually load a large XYZ directly into KnotPlot's GUI**, this patch does not execute anything for you: use `go beadlimit 4000` / `go beadlimit 8000` manually before `go` / `ago`.

## Validation

- Python tests: PASS (counts, 3000 threshold, 3340->4000, 6144->8000, generated command order, installer backup and duplicate guard).
- Integration on supplied v0.4.2d ZIP, with v0.4.3 then v0.4.3a installed in a throwaway copy: PASS; 3340-bead link KPC contains `go beadlimit 4000`.
- 256-resolution same FLAT link: PASS, 835 beads and no new limit command.
- KnotPlot GUI and Windows runtime of this exact patch: **NOT TESTED**.

**Note for Linux-only fixture:** Archive contains a folder `Output` (capital O). Windows resolves that and `output` as the same directory; Linux is case-sensitive. In the integration fixture this was normalized, without altering or repackaging the user's source ZIP.

## Scientific status

Raising the bead allocation limit does not change the knot topology, time-step logic, convergence or physical interpretation. KnotPlot's relaxer is not an inviscid Euler solver, and any existing symmetry / Borromean topology gates remain UNRESOLVED.
