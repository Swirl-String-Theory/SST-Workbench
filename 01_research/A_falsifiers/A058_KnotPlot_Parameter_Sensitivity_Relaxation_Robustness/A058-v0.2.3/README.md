# A058 v0.2.3 — Trefoil GUI-Slider Response + Conditional Runtime Defaults

Purpose: measure one-slider-at-a-time response around the actual KnotPlot runtime defaults for **eight anonymous GUI sliders across six sectors**. Conditional sliders are interrogated only after their owning sector is enabled, fixing the v0.2.2 install failure in which one slider was absent from the bare `reset all` parameter dump.

## Framework

This instance is pinned to `SST_Falsifier_Framework_v1.0.8`. Framework v1.0.8 keeps the v1.0.7 scientific gate semantics but adds run-scoped IDs and non-overwriting output/PDF/ZIP retention. Existing older A058 versions remain pinned to their historical frameworks.

## Regime

- `reset all` supplies the requested Damped baseline dynamics.
- `collision fast` supplies collision avoidance / No Collide.
- No scientific override of fit-to-distance, close, max displacement, splitting, display cadence, or time increment.
- The install test fails closed if the 300-bead trefoil is not safe under that regime.
- One anonymous velocity-dependent lane is intentionally tested under Damped because that is the requested common regime; its private runtime note records that KnotPlot advises Undamped for the velocity-dependent force.

## Sector-context calibration

The install test no longer requires every slider to exist in a naked `reset all` dump. For each sector it performs:

1. `reset all` + collision avoidance;
2. enable exactly that sector;
3. dump `parameters` and read the sliders belonging to that sector;
4. set each slider to `1.25 × runtime_default`;
5. dump `parameters` again and verify the numeric setter stuck.

This is how conditional controls are handled without inventing defaults.

## Adaptive relaxation

There is **no fixed final `ago 1000`, `ago 15000`, or equivalent target**. One persistent KnotPlot process receives `go 32` observation quanta. After each quantum A058 exports a temporary coordinate curve and evaluates successive-window shape and scalar changes. Relaxation stops after four consecutive stable windows (after a minimum warm-up) or at a safety cap. The cap is not interpreted as convergence.

## Campaign size

Six sector references plus `8 × 33` non-default multiplier conditions = **270 conditions**. Each axis uses positive `m=2^(k/4)` for `k=-16..16` with duplicate `k=0` replaced by the matching sector reference, plus an exact-zero endpoint.

## Install test

`run_install.cmd` verifies all eight slider setters in six sector contexts, checks the Damped + No-Collide setup, performs only a `go 1` liveness check, and exports **exactly one trefoil ASCII file**.

## Run

```bat
cmd.exe /c run_pilot_all.cmd
```
