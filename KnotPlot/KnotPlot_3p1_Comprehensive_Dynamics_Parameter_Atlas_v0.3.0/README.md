# v0.3.2 resume note

If a v0.3.1 probe already completed with `175 PASS / 6 RUN_FAILED`, **do not rerun the 181 probes**. Overlay the patch and run:

```bat
run_resume_after_probe.cmd
```

This analyzes the existing probe data and continues only with accepted families.

`drag`/`dragmag` are treated as headless-incompatible when FreeGLUT/window errors
occur; they are excluded from downstream inference rather than aborting the atlas.

---

# v0.3.1 filesystem hotfix

Before the scientific campaign, run:

```bat
run_filesystem_preflight.cmd
```

Expected:

```text
FILESYSTEM PREFLIGHT PASS
```

`run_all.cmd` performs this automatically. The v0.3.0 all-RUN_FAILED result was caused by missing output directories after ZIP extraction, not by the 181 parameter candidates.

---

# KnotPlot 3.1 Comprehensive Dynamics Parameter Atlas v0.3.1

## Purpose

This workbench systematically measures how **dynamics-, relaxation-, numerical-,
discretization-, and selected special-force parameters** in the current KnotPlot
runtime change the trefoil `3.1`.

It is deliberately broader than the earlier MultiDynamics matrix.

### Important scientific distinction

This atlas measures:

- preparation sensitivity;
- artificial KnotPlot relaxation attractors;
- geometry response;
- convergence/path dependence;
- numerical/discretization sensitivity.

It does **not** prove physical vortex-knot stability.

The intended chain is:

```text
KnotPlot Parameter Atlas on 3.1
        ↓
rank parameters + identify null/strong controls
        ↓
select unique representative geometries
        ↓
physical SST finite-core / Biot-Savart / Floquet stability falsifier
```

## Runtime baseline

The baseline is frozen from the supplied `parameters_full.txt`:

```text
mechforce = on
elecforce = on
bendforce = off
charge = 15
hooke = 1
power = 5
tinc = 15
bencon = 1
close = 0.12
max-dr = 0.10
dstep = 1
```

The complete baseline is stored in `parameter_manifest.json`.

## Scope

The atlas contains **45 parameter families** and
**181 candidates per stage**.

Categories:

- `core_force`
- `numerical`
- `secondary_force`
- `geometry_control`
- `discretization`
- `special_dynamics`

Display, camera, export/PostScript, 4-D visualization and catalog-generator
parameters are inventoried but excluded from the dynamics sweep.

## Two-stage campaign

### Stage A — probe

Every candidate runs:

```text
i00000 → i00100
```

The analyzer checks:

- parameter rejection;
- common starting geometry;
- geometry SHA-256;
- polygon length;
- radius of gyration;
- mean/max turning angle;
- non-local distance proxy;
- Kabsch-aligned geometry RMS.

### Stage B — extended

Every **accepted** family, including early nulls, is rerun:

```text
i00000 → i00100 → i01000
```

This deliberately catches parameters whose effect is delayed beyond 100 iterations.

### Classifications

At the 1000-iteration stage:

```text
EFFECTIVE_STRONG
EFFECTIVE_MEDIUM
EFFECTIVE_WEAK
NULL_AT_1000
REJECTED_BY_KNOTPLOT
RUN_FAILED
INVALID_NONCOMMON_START
```

## Run

Extract directly beside `KnotPlot.lnk`, e.g.

```text
C:\workspace\projects\SST-Workbench\KnotPlot\
    KnotPlot.lnk
    KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0\
```

Then:

```bat
run_dry.cmd
run_all.cmd
```

`run_all.cmd` creates:

```text
analysis\PROBE.md
analysis\EXTENDED.md
analysis\probe_metrics.csv
analysis\extended_metrics.csv
analysis\downstream_unique_i01000.csv
KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0_outputs.zip
```

`downstream_unique_i01000.csv` is the bridge to the physical SST stability
falsifier: it contains one entry for each unique 1000-iteration geometry.

## Caution on thermal/stochastic forces

`thermalforce` and `thfstrength` are included for effect discovery, but a
single trajectory is not enough to characterize a stochastic force law.
If they rank as important, the next release should use replicated seeds/runs.

## Deep 10,000-iteration stage

Not run automatically. First inspect the 1000-iteration ranking. A later
numerical-certification stage should take only the strongest and most interesting
families to 10,000+ iterations.
