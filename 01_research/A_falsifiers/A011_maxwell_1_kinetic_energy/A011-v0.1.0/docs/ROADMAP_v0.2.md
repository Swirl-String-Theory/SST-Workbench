# v0.2 roadmap — solver-facing mode extraction

The useful next step is not more statistical machinery; it is connecting this audit layer to an actual resolved SST knot solver.

Priority order:

1. **Geometry importer** for Workbench/Ridgerunner/VortexLab centerlines and resolved tube frames.
2. **Rigid-mode projector** that removes 3 translations and the appropriate global rotational zero directions before internal eigenspectrum analysis.
3. **Finite-difference or automatic-differentiation Hessian interface** for a declared energy functional.
4. **Generalized eigenproblem adapter** for `(H, M)` supplied by the solver.
5. **Mode classifier** using centerline-normal displacement, material-frame twist, core deformation and `Delta Wr` projections.
6. **Encounter projector** that writes the v0.1 CSVs directly from two-knot runs.
7. **Held-out campaign runner** for topology/chirality/orientation grids.

A v0.2 implementation should not invent a core energy functional merely to make the eigenproblem solvable. If the current solver is centerline-only, twist/core gates should remain formally unavailable.
