# A006 v0.4.3b science contract

**Release state: DEVELOPMENT / STATIC_CANDIDATE.**

1. Source individual knot geometries are frozen and unchanged.
2. Per-component in-plane rotations are rigid Euclidean transformations (proper rotations, determinant +1); the original component knot type is invariant *in isolation*. This does not establish preservation of the original whole link under a proposed placement or hypothetical continuous motion.
3. `CENTER` is a finite search over 6_1 component orientations 0/180 degrees, driven by a smoothed curvature proxy and subject to numerical safety gates. The proxy is NOT a certified identification of the topological clasp.
4. The 3-component `5_5_6` and `6_6_5` link topologies, particularly Milnor's triple linking invariant, remain unresolved. Pairwise linking=0 is insufficient.
5. Initial seeds for links are exported solely as header-free three-block `.xyz` with exactly two blank component separators, no redundant `load.kpc` or multicomp KPT.
6. Iterations measured by KnotPlot MD (damped/mech/electrical) are simulation steps, not physical Euler time. Its documented `tanforce` bug is not interpreted as circulation.
7. Mirror operations change chirality geometrically via reflection but do not constitute proof of amphichirality or isotopy classes.
8. Per-resolution datasets must be analyzed for discretization bias. No physical convergence statements without independent tests.
