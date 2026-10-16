# CHANGELOG

## v0.2.2

- Replaces the three-strength design with seven GUI-slider axes across five force sectors.
- Adds sector-matched reference states.
- Uses runtime defaults from the actual KnotPlot executable; no hand-entered strength defaults.
- Fixes regime to documented Damped reset dynamics + `collision fast` (No Collide / collision avoidance).
- Removes fixed final relaxation counts. Production acquisition uses persistent-process adaptive `go 32` windows with a preregistered plateau rule.
- Removes the v0.2.1 `fitto mindist` preconditioning; reset-default trefoil safety is now a fail-closed install gate.
- Explicitly leaves unrelated controls at reset-all values and excludes Grav/Anch/Therm from the study.
- Preserves exactly one trefoil export in the install integration test.
- Adds special diagnostics for S5 parametrization-vs-shape response and S6 convergence-time-vs-final-shape response.
