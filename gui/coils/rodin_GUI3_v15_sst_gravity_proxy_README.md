# rodin_GUI3 v15 — SST gravity/clock proxy overlay

Based on the v13 sub-cell phase GUI.

## Added

A new collapsed side-nav section:

`SST gravity/clock proxy`

Controls:

- Enable SST proxy overlays
- Proxy heatmap quantity
- eta B->u [-]
- Area [cm^2]
- B reference: B p95 / B max / 1 Tesla

## Proxy model

This is research-only visualization, not a gravity-force claim.

The GUI first computes the EM field map B(x,y,z). When SST proxy overlay is enabled, it computes:

```text
u_eff = eta * v_swirl * |B| / B_ref
|p|   = 0.5 * rho_f * u_eff^2
|grad p|
|g|   = |grad p| / rho_f
n_gamma - 1 = 1/sqrt(1-u_eff^2/c^2) - 1
SwirlClock deficit = 1 - sqrt(1-u_eff^2/c^2)
```

Constants used:

```text
rho_f = 7.0e-7 kg/m^3
v_swirl = 1.09384563e6 m/s
c = 299792458 m/s
```

## Important caveat

The GUI does not assert that a coil creates canonical core swirl. `eta` is the explicit calibration/projection parameter. Use this layer for ordering, comparison, and null/falsifier work only.
