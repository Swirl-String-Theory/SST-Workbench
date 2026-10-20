# Static-only PKLSA admission and blocking conditions

E010 v0.3.1 validates static geometrical preparation; E011 v0.3.0 selects `STATIC_READY` anchors. These are **not** Euler or GP dynamic trajectories.

The real E011 archive for `3_1` lists two independent *static* providers: Gilbert ideal geometry and historical KnotPlot relaxed exports. User policy excludes old KnotPlot relaxations from physical inference. Therefore the physically admissible geometry *candidate* currently originates from **one** family only, not two.

A source must supply original bytes matching source_locator.raw_sha256, its exact representation/record, appropriately proven geometry_sha256, a volume/finite-core vorticity initialization, pressure-projection boundary conditions and a mesh-independent phase definition. Its solver must demonstrate time/space/core/solver convergence, energy/helicity/circulation diagnostics and a precommitted held-out frequency prediction. **Only then** can G4–G11 be enabled in a new frozen version.

`D2_vortex_dynamics_handoff: READY` in atlas metadata means *handoff field exists*, **not** a certified 3D dynamic result. No use of rho_c, c, Compton or relativity for clock fits occurs here.
