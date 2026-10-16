# CHANGELOG

## v0.2.3

- Retargets A058 to `SST_Falsifier_Framework_v1.0.8`.
- Fixes the v0.2.2 install failure by interrogating slider defaults **inside each enabled sector context** rather than requiring all sliders in the bare reset-all dump.
- Adds an eighth anonymous slider and sixth sector for the velocity-dependent force; the exact GUI command mapping remains in the private reveal domain.
- Keeps the requested Damped + No-Collide regime. The velocity-dependent lane is explicitly flagged as a Damped compatibility/response test because KnotPlot advises Undamped for that force.
- Expands the campaign from 236 to 270 conditions: 6 references + 8 × 33 perturbations.
- Strengthens runtime state verification: reference and sweep conditions verify sector-context numeric values at both start and final state, not merely marker presence.
- Preserves adaptive `go 32` convergence and the exact-one-trefoil install export.
- Grav, Anch and Therm remain out of scope.

## v0.2.2

- Seven-slider / five-sector adaptive campaign. Install calibration incorrectly required conditional sliders to appear in the bare reset-all dump; user-machine run failed closed at the missing conditional slider, which motivates v0.2.3.
