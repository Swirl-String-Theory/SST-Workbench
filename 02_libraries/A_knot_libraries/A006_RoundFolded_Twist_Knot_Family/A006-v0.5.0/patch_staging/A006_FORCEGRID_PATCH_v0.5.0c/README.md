# A006 ForceGrid v0.5.0c — `amech`, `max-dr` and `close`

Incremental add-on for **A006-v0.5.0a** OR **A006-v0.5.0a plus v0.5.0b**. Does not replace v0.5.0b and does not touch canonical `Output/v050/geometry`, existing 336 campaigns or previous runtime measurements. Each arm starts from *identical* `LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz` (1138+1055+1024=3217 beads).

## Install (in existing project root)

Extract the ZIP under `patch_staging/A006_FORCEGRID_PATCH_v0.5.0c/` and run:

```bat
py -3 patch_staging\A006_FORCEGRID_PATCH_v0.5.0c\install_patch.py --base . --check
py -3 patch_staging\A006_FORCEGRID_PATCH_v0.5.0c\install_patch.py --base . --apply
run_all.cmd FORCEGRID TEST
run_all.cmd FORCEGRID PLAN
```

`BUILD` has already been performed safely by the installer. You can rerun it idempotently:

```bat
run_all.cmd FORCEGRID BUILD
```

Restart KnotPlot so newly added aliases are loaded. Run **one alias at a time** without pressing continuous GUI `go` simultaneously. They are GUI safe (no `stop`) and write independent checkpoints at 0/1/8/32/128.

## Experiments

| Alias | Arm | Mech | Elec | AMECH | Bend | Changed condition |
|---|---|---|---|---|---|---|
| `fgB0` | BEND_OFF | yes | yes | no | off | baseline |
| `fgB1` | BEND_1 | yes | yes | no | 1 | bend sensitivity |
| `fgB10` | BEND_10 | yes | yes | no | 10 | bend sensitivity |
| `fgB100` | BEND_100 | yes | yes | no | 100 | bend sensitivity |
| `fgM` | MECH_ONLY | yes | no | no | off | isolated mech |
| `fgE` | ELEC_ONLY | no | yes | no | off | isolated elec |
| `fgA14` | AMECH_140_ELEC | no | yes | yes | off | linear spring, rest 1.4 |
| `fgAM` | AMECH_MATCH_ELEC | no | yes | yes | off | linear spring, rest = measured median |
| `fgAM0` | AMECH_MATCH_ONLY | no | no | yes | off | isolate linear amech |
| `fgAM2` | AMECH_MATCH_P2 | no | yes | yes | off | nonlinear spring power = 2 |
| `fgD5` | MAXDR_0005 | yes | yes | no | off | max-dr = 0.005 |
| `fgD10` | MAXDR_0010 | yes | yes | no | off | max-dr = 0.010 |
| `fgC10` | CLOSE_010 | yes | yes | no | off | close = 0.10 |
| `fgC30` | CLOSE_030 | yes | yes | no | off | close = 0.30 |

Unless explicitly varied, `close=0.20`, `max-dr=0.02`, `spring-length=1.4`, `afmpower=2`, `bencon=1`, `tinc=15`, `collision fast`, `Damped` **reset default to be confirmed by operator**. The measured median spring is calculated from the actual seed at BUILD time: approximately **1.968625 KnotPlot units**. It is a discretization-derived control, not a physics constant. Force coefficients are kept fixed; do **not** run `mech` and `amech` simultaneously during the isolation experiment.

The source screenshots describe `symm` as an approximation to Greg Buck's symmetric energy, but this patch does not switch it on: doing so would introduce an additional, currently unqualified force law. Damped vs Undamped is also a distinct dynamical comparison and intentionally held fixed.

## First pilot and collision verification

Recommended order: `fgB0`, `fgAM`, `fgA14`, `fgD5`, `fgC30`. The `CLOSE_030` condition increases the collision exclusion distance and can change topological interaction; compare with `fgB0`, not with a different `amech` run. `MAXDR_0005` may simply slow numerical evolution per iteration. Thus compare at fixed iterations **and**, in a later study, similar shape displacement.

The scripts print `collision` and `safe` per checkpoint. Save actual console readback into `Output/qualification_v050c/runs/<ARM>/COLLISION_RUNTIME.txt`; check also **Damped selected in the GUI**. The `collision fast` command is a requested setting, not independent proof of collision safety. Even `safe` is not an invariant certificate.

## Analyze

```bat
run_all.cmd FORCEGRID ANALYZE
```

Output: `Output/qualification_v050c/analysis/component_metrics.csv`, `AUDIT.json`, `AUDIT.md`, and plots **only when real XYZ snapshots exist**. Native KnotPlot CSV format is `/I,/N,/l,/g`; the unsupported `/s` has been removed. The `/l` and `/g` values are multi-component sensitive in this KnotPlot build; use the per-component XYZ measures for conclusions.

Separate direct selection is supported *before preparing a campaign*:

```bat
py -3 tools\force_grid_v050c.py PLAN --arms=AMECH_MATCH_ELEC,MAXDR_0005
```

The installer creates the complete immutable 14-arm plan; to change a previously established plan/checkpoints, use a NEW versioned experiment root instead of overwriting old results.

## Rollback

```bat
py -3 patch_staging\A006_FORCEGRID_PATCH_v0.5.0c\install_patch.py --base . --rollback
```

Rollback refuses to overwrite later manual edits. Only the two original dispatcher/RC files are restored; all measurements are preserved.
