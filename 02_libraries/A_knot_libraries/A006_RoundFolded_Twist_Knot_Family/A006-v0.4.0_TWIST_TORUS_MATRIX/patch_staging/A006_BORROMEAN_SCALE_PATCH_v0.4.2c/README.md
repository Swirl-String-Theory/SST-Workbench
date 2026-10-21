# A006 RoundFolded Borromean v0.4.2c — MIN-bead ladder + uniform scaling

**Target:** Existing Windows A006 `A006-v0.4.0_TWIST_TORUS_MATRIX`, with Borromean patches v0.4.1, v0.4.2, v0.4.2a, **v0.4.2b** already installed.

This is **not a new library/project**, and requires no new KnotPlot shortcut. `run_all.cmd` and all GUI defaults remain unchanged. The installer only replaces:

- `extensions/borromean/whole/build_whole.py`
- `extensions/borromean/whole/run_whole.cmd`
- `extensions/borromean/whole/test_whole.py`

The old files are backed up, original XYZ files are preserved, and new output names end in `_v042c.xyz`.

## Install (from existing project root)

Extract the ZIP under `patch_staging/` and run:

```bat
py -3 patch_staging\A006_BORROMEAN_SCALE_PATCH_v0.4.2c\install_patch.py --base . --check
py -3 patch_staging\A006_BORROMEAN_SCALE_PATCH_v0.4.2c\install_patch.py --base . --apply
run_all.cmd BORROMEAN WHOLE TEST
```

## Build the 256/512/1024 ladder

The **shortest final placed component** is assigned `Nmin` beads. Each other component receives `round(Nmin * L_i/Lmin)` beads, using the final reference-transported polygonal lengths, *before resampling*.

```bat
run_all.cmd BORROMEAN WHOLE BUILD BALANCED MIN 256
run_all.cmd BORROMEAN WHOLE BUILD BALANCED MIN 512
run_all.cmd BORROMEAN WHOLE BUILD BALANCED MIN 1024
```

Default scale for these `MIN` commands is **0.80** (20% smaller in all three coordinates relative to v0.4.2b). Explicit override:

```bat
run_all.cmd BORROMEAN WHOLE BUILD BALANCED MIN 512 0.75
run_all.cmd BORROMEAN WHOLE BUILD ALL MIN 256 0.80
```

`ALL` covers `FLAT`, `SOFT`, `BALANCED`, `TIGHT`. Legacy explicit bead commands and `AUTO TOTAL` remain supported and default to scale 1.0.

Direct Python example:

```bat
py -3 extensions\borromean\whole\build_whole.py --root . --profiles BALANCED --n-shortest 256 --global-scale 0.80
```

### Expected BALANCED counts for scale 0.80

| Minimum component beads | Component 0 (5_2) | Component 1 (5_2) | Component 2 (6_1) |
| ---: | ---: | ---: | ---: |
| 256 | 284 | 264 | 256 |
| 512 | 569 | 527 | 512 |
| 1024 | 1138 | 1054 | 1024 |

Important: final placed `6_1` is shortest here, despite having a longer native seed than `5_2`. `Nmin` refers to actual placed length, NOT knot name.

### Compact output paths

```text
output/borromean/Borromean_5_5_6_BALANCED_MIN0256_S0800_v042c.xyz
output/borromean/Borromean_5_5_6_BALANCED_MIN0512_S0800_v042c.xyz
output/borromean/Borromean_5_5_6_BALANCED_MIN1024_S0800_v042c.xyz
```

Each XYZ has **exactly three numeric blocks**, one empty separator line, no headers, no duplicated closing point. NO KPC and NO KPT are produced. Metadata appears separately in `_REPORT.json`.

### Tube / ring ratio & KnotPlot settings

Scaling the XYZ coordinates alone **does not scale the displayed tube radius in KnotPlot**. To preserve relative tube/ring thickness for `--global-scale 0.80`, adjust existing GUI radius settings separately (if their previous values were):

- `bradius = 0.20 -> 0.16`
- `cradius = 0.10 -> 0.08`
- if `cyl-rad = 0.10 -> 0.08`

For scale-similar contact settings, `close = 0.20 -> 0.16` and `max-dr = 0.02 -> 0.016`. **Changing these does not make the nonhomogeneous KnotPlot force laws dynamically equivalent.** The builder conservatively also requires that segment clearances exceed the *unscaled* `close = 0.20` threshold, so leaving current GUI contact settings at 0.20 does not automatically invalidate static spacing, although the relative-contact ratio changes.

The patch DOES NOT overwrite `knotplotrc` or create any LOAD scripts.

### Tests/status

Tested in a copy of v0.4.0 + patches through v0.4.2b: 12/12 generation runs for `FLAT`, `SOFT`, `BALANCED`, `TIGHT` × minimum 256/512/1024, all with static clearance, cyclic seam and pairwise-linking gates PASS at scale 0.80. Cyclic phase selection avoids short segment artifacts at N=256. KnotPlot runtime and independent component-knot and Borromean Milnor invariants remain UNRESOLVED.
