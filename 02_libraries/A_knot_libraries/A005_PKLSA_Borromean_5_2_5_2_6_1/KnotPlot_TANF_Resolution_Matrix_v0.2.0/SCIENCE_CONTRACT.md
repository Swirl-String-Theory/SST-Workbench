# Scientific contract: resolution and TANF A/B v0.2.0

* Numerical experiments only: 2 knot types × 2 Ns × 2 TANF settings × 9 cumulative snapshots.
* Preserve exact original 1024 source files. Generate 2048 independently from the analytic v0.2.3 source.
* Primary measured axes: cumulative **atomic** KnotPlot AGO iteration, knot type, N, TANF Boolean.
* Fixed controls: KnotPlot dynamics, force magnitudes, collision mode, `close`, `max-dr`, visual settings, exact seed geometry within N.
* Global statistics: filament length, edge CV, max/p99 curvature, radius of gyration, covariance eigenvalues, Kabsch shape RMS, TANF ON-OFF RMS and shape discrepancy between N after arc-length normalization.
* Baseline A/B coordinates must match exactly within the same knot and N. Full and pilot initial geometry must match.
* Topology throughout each dynamics trajectory is UNRESOLVED until a continuous noncrossing trajectory certificate or adequate intermediate checks exist. `safe` or one Dowker code alone is insufficient.
* Runtime condition requiring manual stop: visually pinched/singular clasp, locally collapsing segment distance, loss of knot identity, or numerical instability. Automated KPC scripts cannot fail-close mid-long-AGO without external iteration hooks.
* No finite-core Biot–Savart, no Euler, no evidence for material/solid torus rolling.
