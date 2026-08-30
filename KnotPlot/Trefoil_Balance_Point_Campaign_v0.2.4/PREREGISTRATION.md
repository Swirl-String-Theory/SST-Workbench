# Trefoil Balance Point Campaign v0.2.4 — preregistration

## Objective

Extend the frozen q/h/p ray beyond the v0.2.3 boundary and test the moving
EXPAND/CONTRACT zero through 400k without silently branching from Q20.

## Source fact

All twenty historical v0.2.3 `i00000.txt` coordinate exports are byte-identical:

`2f163170e0c884a75a0da8e9ce1efab4c9863a7eb3b214da92f1caca225e5ded`

Therefore this exact geometry is frozen as `reference/FROZEN_K31_i00000.txt`
and is the cold-start source for every extended-panel setting.

## Frozen extended panel

t values:

`[1.3, 1.31, 1.32, 1.325, 1.33, 1.335, 1.34, 1.345, 1.35, 1.355, 1.36, 1.365, 1.37, 1.375, 1.38, 1.4]`

The first three are overlap controls:
- E01 t=1.30 <-> historical Q18
- E02 t=1.31 <-> historical Q19
- E03 t=1.32 <-> historical Q20

The remaining settings are new and were fixed before any v0.2.4 dynamics.

## Stage A: overlap calibration

E01/E02/E03 are rerun from the common historical i0 geometry to 200k.

Before any new t>1.32 run is allowed:
- |E_new - E_hist| <= 2e-4 per overlap anchor;
- |ΔL_new - ΔL_hist| <= 3e-4;
- |ΔRg_new - ΔRg_hist| <= 3e-4;
- a zero must exist between t=1.31 and 1.32;
- |t*_new(200k)-t*_hist(200k)| <= 0.002.

Historical t*(200k) = `1.315917197379`.

Failure stops the campaign with `OVERLAP_CALIBRATION_FAILED`.

## Stage B: extended cold starts

Only after Stage A passes, all new points t>1.32 are run from the same frozen
i0 geometry to 200k.

Cold starts reproduce the historical centering/checkpoint cadence through 200k.
No new `fitto` or `refine` is applied to the frozen i0 geometry.

## Stage C: 200k -> 400k

All sixteen panel settings continue metric-neutral from their own 200k states.

Checkpoints:
`[220000, 240000, 260000, 280000, 300000, 320000, 340000, 360000, 380000, 400000]`

No `fitto`, `refine`, or `centre` is permitted after loading the 200k checkpoint
and before the first resumed `ago`.

## Late settlement gates

Late window:
`[320000, 340000, 360000, 380000, 400000]`

- |dt*/di| <= 0.001 t per 10k
- last-three t* spread <= 0.0025
- boundary margin = 0.01 from t=1.30 or 1.40

A true geometric fixed-point candidate additionally requires:
- |slope(ΔL/L0 at zero)| <= 7.5e-4 per 10k
- |slope(ΔRg/Rg0 at zero)| <= 7.5e-4 per 10k

## Planning only

Simple geometric-decrement extrapolation from v0.2.3 gives approximately:

`t*(400k) ≈ 1.346404`

This forecast is not an acceptance model.
