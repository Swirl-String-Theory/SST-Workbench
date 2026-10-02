# A047 roadmap after v0.4.0

v0.4.0 deliberately stops before mixing pure-Euler BKM evidence with finite-core SST dynamics.

If S10 shows that no practical `N` can simultaneously resolve the chosen Gaussian core and satisfy the thin-tube curvature bound, the next task is an initialization-method study rather than a larger BKM run.

If one or more geometries pass S10/S20/S22 but fail S50, the result is converged transient amplification and the next useful work is mechanism analysis, not singularity hunting.

If S50 and S60 produce a robust candidate, v0.5.0 should add independent spatial levels, adaptive/independent solver replication, tighter pressure-Hessian/Lagrangian residuals, and only then consider finite-core SST comparison or RPO/Floquet handoff.
