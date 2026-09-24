# E011 SKLSA — Selected Knot/Link Seed Atlas v0.1.0

Purpose: build a deliberately small, deep, KnotPlot-first seed atlas on top of the frozen E010-v0.3.0 identity/source/topology baseline.

## Scope

- all 35 prime knots from 3 through 8 crossings (`3_1` .. `8_21`);
- selected low-crossing links: `L2a1`, `L4a1`, `L5a1`, `L6a1`–`L6a5`, `L6n1`, `L8a1`;
- optional higher-crossing sentinels only: `9_1`, `9_2`, `10_1`, `11_1`, `11_2`;
- no complete 9-, 10- or 11-crossing sweep.

## v0.1.0 gate

This first patch intentionally performs **inventory/discovery**, not seed ranking or dynamics. It answers: which selected canonical topology IDs have which KnotPlot carrier files in the current Workbench?

Run first:

```bat
run_poc.cmd
```

Then the full selected low-crossing inventory:

```bat
run_selected.cmd
```

Outputs are written to `E011_SKLSA_KnotPlot_Selected_v0.1.0-outputs/`.

## Next gate

After the POC inventory is inspected, v0.1.1 should add representation adapters and geometric seed qualification (closure, resampling convergence, curvature/torsion spike diagnostics, self-distance/reach/thickness, and cross-carrier comparison). No single composite best-seed score should be introduced before those component gates exist.
