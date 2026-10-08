# A047 method provenance for A056-v0.4.0

The volumetric `euler_ps3d` provider remains an instance-local adaptation of the audited A047 E010/Euler route: source-native E010 geometry admission, finite-width vorticity seeding, 2/3-dealiased pseudo-spectral incompressible Euler evolution, RK4 time integration and material-marker advection. A056 does not import A047 at runtime and inherits no A047 scientific verdict.

The A056-specific scientific object is different: paired base/perturbed trajectories are registered, projected into a Bishop/material transverse frame, and reduced to the frozen Kelvin residual phase and mode envelope before A056 scoring. v0.4.0 changes only the G2 phase-spectral admission metric; the underlying Euler method provenance is unchanged from A056-v0.3.0.
