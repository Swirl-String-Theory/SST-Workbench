# External PKLSA test sources - truth separation

`reference/PKLSA_TREFOIL_3_1_N300_CENTERLINE.npz` has ordered `points` (300,3), imported without any alteration from the independent KnotPlot-relaxed N300 .txt. Its native geometry units are not independently calibrated to meters. This sample is suitable for static knot tests and a **dimensionless** exploratory Euler pilot; it is NOT a time-resolved PKLSA solution.

`reference/PKLSA_3_1_CANDIDATE_SURFACE.npz` has `vertices_m` (3906,3) and `triangles` (7808,3). It is a closed genus-zero triangle mesh, **not** a material vortex centerline. The importer handles it as a surface and deliberately refuses to run it as a filament.

Source IDs, byte checksums and qualifications are in `reference/PROVENANCE.json`.

To analyse a pre-existing dynamic simulation, supply t, filaments, present, gamma, material_ids and optionally u_vertices and 3D u_grid with x_m,y_m,z_m, plus truthful metadata. Static mesh does not qualify a trajectory.
