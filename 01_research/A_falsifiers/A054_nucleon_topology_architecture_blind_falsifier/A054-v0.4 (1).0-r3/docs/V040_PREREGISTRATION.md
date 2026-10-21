# A054 v0.4.0-r3 preregistration

The protocol is frozen before semantic reveal and before mechanism results are inspected.

1. v0.2 hard thresholds are inherited byte-for-byte through `configs/V020_HARD_GATES_FROZEN.json`.
2. Discovery geometries are the exact 72 anonymous states listed by the successful v0.2 FULL manifest.
3. Confirmation geometries are seven source-native KnotPlot three-component links, but only opaque IDs enter blind scoring.
4. Registered arms: BASE, CORE, ELASTIC, CORE+ELASTIC.
5. Active mechanisms share a global gain chosen from {0.125, 0.25, 0.5, 1.0}; BASIC uses {0.25, 0.5}. No per-case gain fitting.
6. Discovery selection is lexicographic: recovered-cell count, then median log(restoring×ringdown), then lower gain, then arm name.
7. Confirmation reuses the selected arm/gain unchanged and requires recovery on at least two distinct opaque confirmation geometries before G4 can PASS.
8. Recovery means all original v0.2 restoring, Kelvin, ringdown, topology and clearance gates PASS. Relative-equilibrium residual remains diagnostic.
9. RPO/Floquet is never evaluated as a substitute for failed restoring/Kelvin/ringdown; no accepted RPO means no Floquet claim.
10. Current sources are simulation/geometry evidence. Even a G5 numerical PASS cannot by itself open framework G7 physical replication.
