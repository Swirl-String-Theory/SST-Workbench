# A006 RoundFolded Borromean Patch v0.4.2d — 5_5_6 + 6_6_5 + measurements

Base: **the user's uploaded** `A006-v0.4.0_TWIST_TORUS_BORROMEAN_MATRIX.zip` (v0.4.2c already installed). Patch is **in-place** and hash-bound to this exact snapshot.

## Install — inside your existing project root

Unpack this patch so `patch_staging\\A006_BORROMEAN_METRICS_PATCH_v0.4.2d\\install_patch.py` exists.

```
py -3 patch_staging\A006_BORROMEAN_METRICS_PATCH_v0.4.2d\install_patch.py --base . --check
py -3 patch_staging\A006_BORROMEAN_METRICS_PATCH_v0.4.2d\install_patch.py --base . --apply
run_all.cmd BORROMEAN WHOLE TEST
```

No changes to `run_all.cmd`, desktop shortcuts, `knotplotrc.kps`, old XYZ, outputs, or campaign files. Old `build_whole.py` and `run_whole.cmd` backed up to `patch_backups/A006_BORROMEAN_v0.4.2d/`.

## 6_6_5 geometry (two 6_1 + one 5_2)

```
run_all.cmd BORROMEAN WHOLE BUILD665 BALANCED MIN 256 0.80
run_all.cmd BORROMEAN WHOLE BUILD665 BALANCED MIN 512 0.80
run_all.cmd BORROMEAN WHOLE BUILD665 BALANCED MIN 1024 0.80
```

Existing 5_5_6 branch remains:

```
run_all.cmd BORROMEAN WHOLE BUILD BALANCED MIN 512 0.80
```

Profiles: FLAT, SOFT, BALANCED, TIGHT, ALL. Output only `output/borromean/Borromean_6_6_5_BALANCED_MIN0512_S0800_v042d.xyz` and `..._REPORT.json`; no KPC/KPT/component XYZ. The .xyz contains **three numeric-only components with exactly one blank line between blocks**. Component order for 6_6_5: 6_1 / 6_1 / 5_2.

No topological certification is implied by the name 'Borromean'. Individual knot polynomials after transport, Milnor mu123 and true 3-component isotopy remain **UNRESOLVED**.

## Optional native KnotPlot measurement CSV (without load scripts)

First open the **.xyz manually** in KnotPlot. Check `close`, `information`, `lnknum`; use `close all` if KnotPlot marks components open. Use your own controlled dynamics configuration (e.g. damped, `collision fast`, `close = 0.20`, `max-dr = 0.02`).

Generate *measurement-only* commands:

```
run_all.cmd BORROMEAN WHOLE METRICS 665 BALANCED 512 OFF
```

Run these commands **after manually loading** the matching XYZ:

```
read output/borromean/metrics/Borromean_6_6_5_BALANCED_MIN0512_S0800_v042d_OFF_MEASURE_ONLY.txt
```

This file does **not** load geometry or generate/import a KPC/KPT. It writes `data open ...csv`, `data format`, `data header`, `length`, `rog`, `safe`, `lnknum`, `data`, and atomic `ago` steps at iterations 0, 1, 8, 32, 128, 512, 1000, 2000, 4000 and 8000. It changes `tanforce` only; the rest of the dynamics configuration must be held fixed by the operator. To repeat with `tanforce=on`, reload the exact same XYZ manually and generate `... METRICS 665 BALANCED 512 ON`. Do **not** confuse KnotPlot relaxation with Euler/Biot–Savart.

The native scalar CSV is designed with known five columns: iteration, nbeads, length, rog, safe. `lnknum` is recomputed to the console at each checkpoint; this is **not** an automatic Milnor invariant or a logged full matrix. KnotPlot documents `/W` (space writhe) and `/F` (linking information), but their exact update and output behavior is not verified for your installed release. They remain a separate qualification task, rather than silently supplying stale values. To generate a **separate, explicitly experimental raw stream** for `/W` and `/F`, use:

```
run_all.cmd BORROMEAN WHOLE METRICS_EXT 665 BALANCED 512 OFF
```

Then (after a fresh manual load, from iteration zero) read the emitted `*_EXTENDED_UNVERIFIED_MEASURE_ONLY.txt`. Its output is named `*_EXTENDED_RAW.csv`, is deliberately **not included** in quantitative plots, and must first be checked against the KnotPlot console and confirmed writhe-calculation behavior for your installed version. It includes `lnknum` and `acn` calculation commands, but this is not certification that `/W` and `/F` values were refreshed; a separate runtime check remains mandatory.

## Analysis

```
run_all.cmd BORROMEAN WHOLE ANALYZE
```

Writes `output/borromean/analysis_v042d/component_geometry.csv`, `pairwise_gauss_approx.csv`, `native_knotplot_matrix.csv` (only if runtime CSV exists), PNG line charts (only if native CSV exists), and `AUDIT.json`. The component metrics include length, cyclic closure edge ratio, bead spacing uniformity, max/p95 discrete curvature. The Gauss result is a midpoint approximation for pairwise linking only; it is not a Milnor triple-link test.

## Validation and restrictions

- Static build/tests on source ZIP: qualified as static candidates (not certified 3-component links).
- Windows `run_all` integration, KnotPlot `data` CSV syntax in the user's installed version, native runtime: **NOT TESTED**.
- An absence of runtime records produces `NO_KNOTPLOT_RUNTIME_DATA`; no measurements are invented.
- Source hashes prevent installing on other versions or twice. Copy over older output files is refused.
- `metrics_native.py` generates `.txt` measurement instructions, **not** a LOAD.kpc. No separate per-component XYZ ever written.
