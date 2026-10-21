# A006 RoundFolded NearUnknot v0.2.3 — Smooth Clasp Repair

**Status: DEVELOPMENT / STATIC_CANDIDATE.** No KnotPlot runtime, topology-through-time, Euler, PKLSA, toroidal-roll or vortex stability validation in this environment.

## What changed from v0.2.2

This is a real, standalone build, based on the provided `build.py`, `knotplotrc(1).kps`, and `KnotPlot(1).lnk` and the v0.2.2 source modules. The original uploaded files are preserved in `inputs/`. For the `5_2` and `6_1` TikZ-derived smooth curve, this release:

- Makes the lower clasp less pinched **without inserting a separate knot blob**. The angular-dependent, strictly positive radial map is a continuous family of injective mappings on an annulus.
- Widens 3D crossing-lift bumps (`width=0.020` rather than `0.011` of the total normalized parameter) to avoid narrow geometric bends. Revalidates actual projected crossings, alternating over/under and Alexander determinant after each resampling.
- Samples the closed 3D curve using a periodic arc-length cubic interpolant. Fails on unequal spacing, invalid crossing assignment, or insufficient segment clearance.
- Retains your `show backdrop`, `mode cbf`, `bradius = 0.2`, `cradius = 0.1`, `tanf = on`, `tanmag = 9`, `stusplit = 0`, `dstep = 1`, `close = 0.20`, `max-dr = 0.02`. The KnotPlot `go` runs are separate **manual** operations.
- **Omits `fitto avlength 0.5`** from standard loads and from the versioned `sstbase` startup alias: it changes the imported geometric scale, which would invalidate the precomputed `close`-relative clearance. The original user RC has been retained unchanged.
- Includes an optional PowerShell utility to create a **new** shortcut from the uploaded `.lnk` using the actual installed executable, with the extracted v0.2.3 project folder as the new `WorkingDirectory`. The user's old shortcut is never modified.

## Installation (Windows)

Suggested target location:

```
C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.2.3_SmoothClasp
```

Unzip into that folder, **without placing a second project folder inside it**. The folder containing `run_all.cmd` is the project root.

```cmd
python -m pip install -r requirements.txt
run_all.cmd SMOKE
run_all.cmd BASIC
run_all.cmd FULL
```

If `(venv)` is active, `run_all.cmd` uses its `python`. `SMOKE` makes N=256, `BASIC` makes N=512 and `FULL` makes N=1024. `ALL` produces all 18 cases. Each run tests code before generating; the output directory is version-local and does not overwrite v0.2.2.

### Fix your KnotPlot shortcut to this version (recommended)

From **Windows PowerShell** in the extracted root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\Update-KnotPlotShortcut.ps1
```

This creates `KnotPlot_A006_v0.2.3_SmoothClasp.lnk` with `WorkingDirectory` equal to the extracted project folder. It reads the executable target from `inputs/KnotPlot_original.lnk`, checks that the `.exe` is present, and fails closed otherwise. If an output shortcut already exists, it is backed up. The uploaded original points to a v0.2.2 working directory, not this release.

If KnotPlot was relocated to a different installation, supply a *working* original `.lnk` via `-OriginalShortcut`. **The tool does not install KnotPlot and cannot run Windows COM on Linux.**

### RC and aliases

The original `inputs/knotplotrc_original.kps` has not been modified. This version provides:

- `presets/sst_smoothclasp_v023.kps`: aliases to load after startup manually (`read presets/sst_smoothclasp_v023.kps`).
- `presets/knotplotrc_v023_COMPLETE.kps`: original settings and unrelated aliases, with the near-unknot aliases updated and `sstbase` without `fitto`.
- Optional installer (explicit RC path, backup first):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\Install-AliasesOptional.ps1 -KnotplotRc "C:\path\to\YOUR\knotplotrc.kps"
```

Aliases: `52S512` = 5_2 SOFT, `52B512` = 5_2 BALANCED, `52Q512` = 5_2 TIGHT, analogous `61S512`/`61B512`/`61Q512`. Old `52N512`/`52R512`/`52T512` are mapped to the updated TIGHT/SOFT/BALANCED release paths, respectively. Alias paths depend on having the correct working directory.

## KnotPlot smoke tests — load from the new shortcut

For 5_2 SOFT at N=512:

```text
read output/individual/SmoothClasp_5_2_SOFT_N0512/SmoothClasp_5_2_SOFT_N0512_LOAD.kpc
```

Or for 6_1 BALANCED at N=512:

```text
read output/individual/SmoothClasp_6_1_BALANCED_N0512/SmoothClasp_6_1_BALANCED_N0512_LOAD.kpc
```

Run these **separately, waiting until each operation has finished**:

```text
read output/individual/SmoothClasp_5_2_SOFT_N0512/SmoothClasp_5_2_SOFT_N0512_SNAP_BEFORE.kpc
read output/individual/SmoothClasp_5_2_SOFT_N0512/SmoothClasp_5_2_SOFT_N0512_GO1.kpc
read output/individual/SmoothClasp_5_2_SOFT_N0512/SmoothClasp_5_2_SOFT_N0512_SNAP_AFTER1.kpc
read output/individual/SmoothClasp_5_2_SOFT_N0512/SmoothClasp_5_2_SOFT_N0512_GO32.kpc
read output/individual/SmoothClasp_5_2_SOFT_N0512/SmoothClasp_5_2_SOFT_N0512_SNAP_AFTER33.kpc
```

Then in Windows Command Prompt or Powershell in project root:

```cmd
python tools\analyze_knotplot_snapshots.py 5_2 SOFT 512
```

Repeat for `6_1` / BALANCED / TIGHT as required. Comparing before/after checks finite segment clearance, crossing count, alternating diagram, determinant, and point displacements. The report explicitly does **not** prove that no crossing happened between snapshots. Neither does `go` represent inviscid Euler or finite-core Biot–Savart.

## Profiles

| Profile | Global radial compression | Bottom-pocket compression | Bottom angular width | Suggested cosmetic cylinder radius |
|---|---:|---:|---:|---:|
| SOFT | 0.19 | 0.62 | 0.55 rad | 0.07 |
| BALANCED | 0.16 | 0.44 | 0.45 rad | 0.06 |
| TIGHT | 0.12 | 0.30 | 0.35 rad | 0.045 |

`SOFT` is recommended for the first `go` run. `TIGHT` is a *more demanding* test, **not certified dynamically safe**. The supplied KPC loads preserve your `bradius` and `cradius` settings, independent of the cosmetic tube suggestions in the reports.

## Versioning / limitations

This is a standalone A006 release candidate. The 0.2.1 TikZ reconstruction is a periodic cubic approximation to Hobby, not an exact reproduction. No Borromean composites are built or promoted in this version. The original v0.2.2 source code and user files have not been modified. Results use arbitrary KnotPlot coordinate units; they do not set SST physical core radius `r_c`.

## Sources

\bibitem{SchareinKnotPlotManual} R. G. Scharein, *KnotPlot Manual*, Hypnagogic Software, https://knotplot.com/manual/.

\bibitem{Conway1970} J. H. Conway, ``An Enumeration of Knots and Links, and Some of Their Algebraic Properties,'' *Computational Problems in Abstract Algebra*, Pergamon (1970), pp. 329--358. DOI: 10.1016/B978-0-08-012975-4.50034-5.