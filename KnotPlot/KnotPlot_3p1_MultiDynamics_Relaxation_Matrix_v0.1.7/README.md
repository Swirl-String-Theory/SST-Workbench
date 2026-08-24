# KnotPlot 3.1 MultiDynamics Relaxation Matrix v0.1.7

## Why v0.1.7 is necessary

The earlier matrix contained a real KnotPlot syntax defect:

```text
charge 15
hooke 1
power 6
timeincr 15
```

KnotPlot interpreted these as commands. Target logs consequently reported
`unknown command`.

The saved runtime parameter dump shows the correct model:

```text
charge = 15
hooke = 1
power = 6
tinc = 15
```

`nbeads 300` is also obsolete; v0.1.7 uses:

```text
refine nbeads 300
```

## Scope

v0.1.7 preserves the **41-candidate scientific design** of the earlier matrix:

- 1 MEB baseline
- 4 force-ablation candidates
- 5 charge/ME candidates
- 5 bencon/MB candidates
- 5 power/ME candidates
- 5 close/MEB candidates
- 5 hooke/ME candidates
- 5 max-dr/MEB candidates
- 5 tinc/MEB candidates
- 1 charge-anneal MEB schedule

Each ordinary candidate starts independently from `3.1` and records:

```text
i00000
i01000
i04000
i10000
```

The anneal schedule remains:

```text
q=60 @ 0..1000
q=30 @ 1000..2500
q=15 @ 2500..4500
q=7.5 @ 4500..7000
q=0 @ 7000..10000
```

but now each charge change is a valid `charge = value` assignment.

## Run

Place beside `KnotPlot.lnk`, then:

```bat
run_all.cmd
```

Recommended first target-machine check:

```bat
run_00_install.cmd
run_05_generate.cmd
run_10_validate_syntax.cmd
run_20_smoke_first.cmd
```

Only after the first 10k candidate passes should you run:

```bat
run_30_matrix.cmd
run_40_analyze.cmd
```

## Relationship to Atlas v0.3.1

Matrix v0.1.7 is the **deep core matrix** (41 candidates, 10k iterations).
Atlas v0.3.1 is the **broad discovery atlas** (45 families / 181 candidates,
100 then 1000 iterations).

Use both; they answer different questions.
