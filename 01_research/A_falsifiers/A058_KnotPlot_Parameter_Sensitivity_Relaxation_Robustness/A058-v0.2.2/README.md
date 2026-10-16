# A058 v0.2.2 — Trefoil GUI-Slider Response + Adaptive Relaxation

Purpose: measure one-slider-at-a-time response around the actual KnotPlot runtime defaults for seven anonymous GUI sliders. The production run uses one catalogue trefoil, five sector-matched references, and a quarter-octave multiplier ladder.

## Regime

- `reset all` supplies the documented damped default dynamics.
- `collision fast` supplies collision avoidance / No Collide.
- No scientific override of fit-to-distance, close, max displacement, splitting, display cadence, or time increment.
- The install test fails closed if the 300-bead trefoil is not safe under that regime.

## Adaptive relaxation

There is **no fixed final `ago 1000`, `ago 15000`, or equivalent target**. One persistent KnotPlot process receives `go 32` observation quanta. After each quantum A058 exports a temporary coordinate curve and evaluates successive-window shape and scalar changes. Relaxation stops after four consecutive stable windows (after a minimum warm-up) or at a safety cap. The cap is not interpreted as convergence.

## Campaign size

Five sector references plus 7 × 33 non-default multiplier conditions = **236 conditions**. Each axis uses positive `m=2^(k/4)` for `k=-16..16` with the duplicate `k=0` replaced by the sector reference, plus an exact-zero endpoint.

## Install test

`run_install.cmd` verifies all seven slider setters, resolves five sector booleans from the actual runtime parameter dump, checks the Damped + No-Collide setup, performs only a `go 1` liveness check, and exports **exactly one trefoil ASCII file**.

## Run

```bat
cmd.exe /c run_pilot_all.cmd
```
