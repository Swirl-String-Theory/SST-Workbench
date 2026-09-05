# Changelog

## v0.2.0
- Promotes the action test from externally supplied observables to a raw-geometry centerline campaign.
- Adds C++17/pybind11 regularized Biot–Savart velocity and line-energy kernels plus Python parity fallback.
- Adds strict provenance classification of the `4*pi^2*rho_core*v*r_c^4=h` identity.
- Removes `rho_core` and `F_swirl_max` from the pre-reveal action path.
- Adds h-free SI scaling using `rho_f`, `r_c`, and `Gamma_c`.
- Adds best-rigid-motion relative-equilibrium residual.
- Adds matched +/- broadband perturbations, discovery-only POD and frozen holdout frequency extraction.
- Adds explicit classical `J~A^2` continuity null so discrete frequencies cannot masquerade as quantized action.
- Adds a positive resolved-energy gate; negative/underflow-clipped excitation energies can no longer create a false universal action PASS.
- Uses RK4, CFL-like `dt ~ ds^2`, fixed final time, substep guard and scheduled arclength reparameterization.
- Adds separate temporal-refinement and spatial-resolution convergence gates.
- Adds dynamic timestep recomputation from current minimum spacing and exact-time reparameterization/sample events.
- Adds anonymous carrier IDs and quarantines raw identity-bearing observations outside BLIND archives.
- Adds private blind key commitments and separate reveal command.
- Keeps external Wien field–matter closure CSV gate for independently generated mass/pressure/statistical observables.
- Adds trust-model documentation and fail-closed non-claims inherited from prior SST workbenches.
