# A050 v0.3.0 — PKLSA Real-Geometry Transfer + Source-Independence Gate

This release replaces the synthetic primary carrier used in v0.2.x with provenance-qualified external geometry staged from the SST-Workbench PKLSA evidence graph.

## Scientific question

Does the long-horizon transverse-mode / pressure-memory structure survive transfer from generated reference curves to independently sourced, real 3-D embeddings of one fixed knot topology?

The primary panel is frozen before dynamics. Source identity is hidden from the blind runner. Four PKLSA-qualified historical KnotPlot relaxation states and the one available independent Gilbert ideal reference form the primary upstream panel. Two QHP carriers are diagnostic only and do not count as an independent upstream provider.

The current PKLSA v0.3.1 source snapshot reports 189 qualified carriers and two strict upstream provider groups. It reports no admitted Ridgerunner carrier, so v0.3.0 does **not** pretend to contain a Ridgerunner cross-check.

## Primary gate

Each external base geometry is run for 2048 dimensionless steps. Five fixed transverse holdouts at RMS amplitude 0.00125 are generated per primary base. A base is robust only when the unperturbed baseline passes the inherited modal-persistence gate and at least 4/5 holdouts preserve the same persistent branch. The anonymous source groups must satisfy 2 robust bases in S01 and 1 robust base in S02.

No mode number is targeted. In particular, the prior m=3 observation is descriptive only and is not a v0.3.0 acceptance criterion.

Pressure-field temporal memory is evaluated on the five primary baselines over 1024 steps. The prior memory thresholds are unchanged. At least 3/5 bases must retain memory and at least 2/5 must meet the convergence criterion.

## What a PASS means

A PASS would show that the effect is not confined to the synthetic G0002 parametrization: robust modal persistence would have transferred across two independent upstream geometry providers while temporal memory also survived on a majority of the real-geometry panel. This is substantially stronger structural evidence, but it is still **not** a validation of SST or an identification of an absolute Kelvin-wave speed.

## What a FAIL means

A modal-transfer failure would support the interpretation that the v0.2.x coherent branch was representation/trajectory-specific rather than a robust property of externally sourced knot geometry. A memory-only survival with modal failure would separate the pressure-memory mechanism from a coherent phase-clock mechanism.

## Run

From this version directory inside SST-Workbench:

```bat
run_all.cmd
```

The script auto-detects the Workbench root. Alternatively set `SST_WORKBENCH_ROOT` or pass the root as the first argument.

`run_all_extended.cmd` is a non-primary high-resolution replication. Do not use it to replace or rescue the frozen primary verdict.
