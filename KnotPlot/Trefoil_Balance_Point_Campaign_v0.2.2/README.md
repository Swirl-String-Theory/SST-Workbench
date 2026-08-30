# Trefoil_Balance_Point_Campaign_v0.2.2

Metric-neutral continuation of the repaired v0.2.1 K31 q/h/p sweep.

## Run

Put this folder next to the repaired:

```text
Trefoil_Balance_Point_Campaign_v0.2.1
```

and run one line:

```bat
run_all.cmd
```

The importer automatically reads the sibling v0.2.1 `out` folder. If your source
is elsewhere:

```bat
set TREFOIL_V021_SOURCE=C:\path\to\Trefoil_Balance_Point_Campaign_v0.2.1
```

or point it at the repaired v0.2.1 outputs ZIP.

## Pipeline

```text
install
-> verify preregistration
-> import 0..60k history + i60000 states
-> generate frozen 60k probes + continuation KPCs
-> verify KPC syntax/metric-neutral prefix
-> reload all 20 i60000 states without geometry transforms
-> verify L and Rg continuity
-> continue all 20: 60k->70k->80k->90k->100k
-> analyze zero-track velocity and fixed-state E gates
-> pack outputs
```

## Critical resume rule

After:

```text
load ..._i60000.k
```

v0.2.2 does **not** execute:

```text
fitto
refine
centre
```

before the first resumed `ago`.

The separate reload probe must match the original 60k length and radius of
gyration to relative tolerance `2e-5`.

## New primary scientific gate

The old fixed-state E gate is retained, but is no longer sufficient by itself.

At 70k,80k,90k,100k the interpolated expansion/contraction zero must exist.
For a settled result:

```text
abs(dt_zero/di) <= 0.0010 t per 10000 iterations
last-three t_zero spread <= 0.0025
```

If the zero is still trackable but fails these limits, the primary result is:

```text
MOVING_LATE_BALANCE_ZERO
```

This directly tests whether the balance point is asymptotically settling rather
than merely passing slowly through the frozen q/h/p panel.

## Additional diagnostics

`ΔL/L0` and `ΔRg/Rg0` are reported separately so cancellation inside

```text
E = 0.5 * (ΔL/L0 + ΔRg/Rg0)
```

is visible.

No new q/h/p setting is introduced in this release.
