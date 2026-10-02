# SST Adaptive Period-Aware RPO + Multiple-Shooting + Floquet Blind Falsifier v0.1.0

This is **one falsifier with sequential rungs**, not several disconnected falsifiers.

## Question

For trefoil preparations that already passed the v0.4.8 P0/P1/P2/P5 screen, is the P7 failure caused by a too-short / too-narrow RPO search, or is there genuinely no certifiable recurrent nonlinear orbit in the preregistered neighborhood?

## Default inputs

v0.4.8:

```text
C:\workspace\projects\SST-Workbench\SST_Trefoil_Lobe_Orientation_Blind_Falsifier\SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact
```

KnotPlot atlas:

```text
C:\workspace\projects\SST-Workbench\KnotPlot\KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0
```

Override them without editing code:

```bat
set SST_V048_DIR=C:\path	o0.4.8
set SST_ATLAS_ROOT=C:\path	otlas
```

## Rungs

### R1 — deterministic selection

Selects only previous v0.4.8 screen candidates with:

```text
P0 = PASS
P1 = PASS
P2 = PASS
P5 = PASS
```

The default deterministic campaign excludes `thermalforce` and `thfstrength`. With the supplied screen this is expected to select `charge=60` and `hooke=0.5`, but the selection is recomputed from the local output instead of hard-coded.

If adaptive spectral results already exist, only `SPECTRAL_CONVERGED_* : PASS` candidates are retained. Otherwise the final report explicitly says `SPECTRAL_PENDING`.

### R2 — period-aware multimode scan

For each positive-imaginary oscillatory eigenpair:

\[
T_{pred} = 2\pi / |\Im\lambda|.
\]

`T_pred` controls **only the observation horizon**. It is never inserted into the equations of motion as a restoring frequency.

The scan uses fixed amplitude and phase grids. It keeps the strict v0.4.8/R5 closure gate:

```text
excursion >= 0.0075
recurrence <= 0.025
return / peak <= 0.50
no core event
```

### R3 — reduced multiple shooting

Only preregistered near-return seeds are promoted. The candidate period is first searched on a fixed discrete scale grid. The orbit is split into 3 (basic) or 4 (extended) shooting segments. Matching corrections are solved in a low-dimensional TBK/Kelvin mode subspace by damped finite-difference least squares.

The shooting algorithm **does not relax the RPO gates**. A shooting candidate still has to make an excursion and close under the same recurrence and return-ratio limits.

### R4 — Floquet

Only a shooting-certified RPO is passed into the **actual v0.4.8 `floquet_multi` implementation**. The central certification uses the R5 value:

```text
panel_floquet_eps = 0.00075
rho_non-neutral <= 1.03
```

Extended mode also evaluates 0.000375 and 0.0015 as numerical diagnostics; they do not replace the central gate.

## Commands

Fast diagnostic:

```bat
run_basic.cmd
```

Recommended full RPO search:

```bat
run_extended.cmd
```

One-click default:

```bat
run_all.cmd
```

Optional thermal/stochastic branch (kept scientifically separate):

```bat
run_stochastic_branch.cmd
```

Runtime setup:

```bat
run_install.cmd
```

Dry/static validation:

```bat
run_dry.cmd
```

Basic one-click:

```bat
run_all_basic.cmd
```

## Resume

Every individual multimode scan cell is cached. A long run can be restarted without discarding completed cells.

```bat
run_resume_from_refine.cmd
```

## Important interpretation

A `NO_CERTIFIED_RPO` result means:

> no RPO was certified in the preregistered eigenmode × amplitude × phase × period-horizon domain.

It does **not** prove that the full Euler/finite-core state space contains no RPO.

Likewise, `RPO_FLOQUET_BOUNDED_SPECTRAL_PENDING` is not yet a complete stability certification. The existing N=720 adaptive high-k spectral ladder remains independent and mandatory for the strongest SST stability claim.
