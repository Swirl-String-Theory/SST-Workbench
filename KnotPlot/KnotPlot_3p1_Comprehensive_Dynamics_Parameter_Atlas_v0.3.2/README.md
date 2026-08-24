# KnotPlot 3.1 Comprehensive Dynamics Parameter Atlas v0.3.3


## v0.3.3 analysis correction + balance candidates

No KnotPlot dynamics are changed and no completed relaxation needs to be rerun.

v0.3.3 replaces the effect-size classification metric by:

1. uniform closed-curve arclength resampling (256 samples);
2. search over all cyclic curve origins;
3. proper Kabsch rotation;
4. normalized RMS using mean radius of gyration.

The old bead-index metric is retained as `legacy_indexed_normalized_rms`.

This specifically prevents tangential bead redistribution from masquerading as
large physical shape change.

v0.3.3 also derives a **surrogate** `charge × hooke × power` balance ray from
the one-factor endpoint responses. This is explicitly a candidate generator,
not proof of instantaneous force balance.

For a completed v0.3.2 campaign, overlay the patch and run:

```bat
run_reanalyze_v033.cmd
```

No `ago` command or KnotPlot executable is invoked by that script.


## v0.3.2 isolated-run-failure continuation

The first target v0.3.1 probe produced:

```text
PASS=175  REJECTED=0  RUN_FAILED=6
```

All six failures are confined to `drag` / `dragmag`.

For a discovery atlas, an isolated candidate runtime failure is itself a
measured outcome. v0.3.2 therefore records `RUN_FAILED` candidates and continues
when their fraction is <= 10%. A larger failure fraction still aborts as a
runtime/infrastructure safety condition.

If the v0.3.1 probe has already completed, do **not** rerun it. Overlay the
v0.3.2 patch and run:

```bat
run_15_diagnose_run_failed.cmd
run_resume_after_probe.cmd
```

The resume script reuses `out\probe` and `logs\probe`, builds `PROBE.json`, then
runs only accepted families in the 1000-iteration extended stage.

## Definitive syntax-verified rebuild

This release uses the saved KnotPlot runtime dump `parameters_full_source.txt` as
the authority for assignable parameter names. This resolves the ambiguity found
in the older MultiDynamics scripts:

```text
charge 15       # WRONG: parsed as an action command
charge = 15     # parameter assignment

hooke 1         # WRONG
hooke = 1       # parameter assignment

power 6         # WRONG
power = 6       # parameter assignment

timeincr 15     # WRONG name
tinc = 15       # actual runtime parameter
```

Action commands keep their literal KnotPlot syntax:

```text
reset all
load 3.1
refine nbeads 300
mode cb
centre
fitto mindist 1.05
collision fast
energy model MD
ago 100
```

## Scope

The atlas contains **45 parameter families / 181 candidates per generated
stage**, derived from the supplied runtime parameter dump.

Stage A:

```text
i00000 -> i00100
```

Stage B reruns all families that KnotPlot accepted in Stage A:

```text
i00000 -> i00100 -> i01000
```

Rejected parameters remain a measured atlas result rather than crashing the
whole campaign.

## Run

Extract beside `KnotPlot.lnk`:

```text
...\KnotPlot\
    KnotPlot.lnk
    KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.1\
```

Then:

```bat
run_all.cmd
```

The chain is:

```text
install
-> filesystem preflight
-> generate 181+181 KPC scripts
-> static runtime-manifest/syntax audit
-> Python selftest
-> 100-iteration probe
-> probe analysis
-> 1000-iteration accepted-family stage
-> extended analysis
-> output ZIP
```

For a no-KnotPlot check:

```bat
run_00_install.cmd
run_00_generate.cmd
run_dry.cmd
```

## Scientific role

The atlas is a **preparation/dynamics-discovery instrument**, not a physical SST
stability proof. Its output should be deduplicated before downstream physical
falsifiers.

The compact `KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.7` is the
10,000-iteration core companion. Use the Atlas to discover controls; use the
Matrix to deeply characterize the selected canonical controls.
