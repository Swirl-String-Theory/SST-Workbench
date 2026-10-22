# A006 v0.5.0b — Controlled Force Qualification

**INCREMENTAL PATCH on `A006-v0.5.0a_ROUNDFOLDED_REBUILD`**, not on v0.4.x. Keeps existing KnotPlot shortcut and project root. Does **not** edit existing 336 campaigns, masters, three-block XYZ geometry, or prior outputs.

## Research design

All arms load exactly the same fixed seed, `Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz` (3 components, 3217 beads). Six independent starts:

| Arm | elecforce | mechforce | bendforce | bencon |
|---|---|---|---|---:|
| `BEND_OFF` | ON | ON | OFF | 1 (inert) |
| `BEND_1` | ON | ON | ON | 1 |
| `BEND_10` | ON | ON | ON | 10 |
| `BEND_100` | ON | ON | ON | 100 |
| `MECH_ONLY` | OFF | ON | OFF | 1 (inert) |
| `ELEC_ONLY` | ON | OFF | OFF | 1 (inert) |

Common: `tanforce=off`, `amechforce=off`, `tinc=15`, `max-dr=0.02`, `close=0.20`, `collision fast`, `energy model MD`, `hooke=1`, `charge=15`, `power=5`. The scripts query `collision` and `safe` at each checkpoint. **Do not treat the requested collision mode as verified** until the GUI console readback is saved. Damping follows reset defaults; confirm visually in your build.

## Install

Unzip into `patch_staging/A006_FORCEQUAL_PATCH_v0.5.0b/` inside the existing A006 v0.5.0a project root.

```bat
py -3 patch_staging\A006_FORCEQUAL_PATCH_v0.5.0b\install_patch.py --base . --check
py -3 patch_staging\A006_FORCEQUAL_PATCH_v0.5.0b\install_patch.py --base . --apply
run_all.cmd FORCEQUAL TEST
run_all.cmd FORCEQUAL PLAN
run_all.cmd FORCEQUAL BUILD
```

Restart KnotPlot so `knotplotrc.kps` aliases are reloaded. Enter each alias separately (`fqB0`, `fqB1`, `fqB10`, `fqB100`, `fqM`, `fqE`), or run a direct script:

```text
read Output/qualification_v050b/scripts/FQ_BEND_1.kps
```

`read` scripts are GUI-safe: **no `stop`**. Each is complete with native CSV `/I,/N,/l,/g` (no unsupported `/s`), data close, atomic `ago` checkpoints 0/1/8/32/128, `go beadlimit 4000` and XYZ snapshots. **Do not click the continuous GUI go button concurrently with the script.** Start each test afresh from its alias; do not run a second alias while the first is in progress.

`BEND_100` and `MECH_ONLY` may change geometry quickly. You can generate shorter scripts by command-line:

```bat
run_all.cmd FORCEQUAL BUILD --maxIteration=8 --checkpoints=0,1,8
```

**Note:** This changes the plan and is only allowed before an existing `PLAN.json` with different checkpoints exists. For a short pilot, use a fresh copy of A006 v0.5.0a or run only the first checkpoint stages manually on a copy of the script.

After finishing the six runs:

```bat
run_all.cmd FORCEQUAL ANALYZE
```

The analyzer reads actual XYZ snapshots (including KnotPlot `Component n:` headers), compares 3 components at each checkpoint, computes discrete turning angles, edge length statistics and curvature, and checks the zero-step data are byte-equivalent after parsing. It will **not create simulated data**.

Copy the actual KnotPlot console readback containing `collision` results, `safe` reports and any warnings to each arm's `Output/qualification_v050b/runs/<ARM>/COLLISION_RUNTIME.txt`. This is an **operator-captured log, not a machine-authenticated KnotPlot trace**. If absent, the report explicitly says `UNVERIFIED_NO_CONSOLE_RECORD`.

**Do not mistake the native `/l` for total multicomponent link length**; the audited KnotPlot build reports last-component length. `/g` is a sum of component gyration values. Use `analysis/component_metrics.csv` for component measurements.

## Rollback

```bat
py -3 patch_staging\A006_FORCEQUAL_PATCH_v0.5.0b\install_patch.py --base . --rollback
```

`run_all.cmd` and `knotplotrc.kps` are restored from `patch_backups/v050b_FORCEQUAL`, while qualification data are retained.

## Important existing limitation

The **old v0.5.0a campaigns still contain `data format "/I,/N,/l,/g,/s"`**. That field is unsupported by your local KnotPlot; this focused patch intentionally **does not alter** the prior 336 campaigns. Fix those in a separate versioned migration before executing the full production matrix.
