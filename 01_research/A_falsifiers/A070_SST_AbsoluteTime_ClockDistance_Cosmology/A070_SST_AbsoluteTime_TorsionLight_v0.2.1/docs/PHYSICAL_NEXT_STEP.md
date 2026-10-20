# Physical next stage - must not be promoted by synthetic blind success

## Source-native finite-core input required

For each independently supplied PKLSA seed: provenance, source identifier, geometry topology, spatially resolved 3D fluid velocity u(x,t), vorticity curl u, pressure field or pressure-Poisson closure, core radius profile a(s,t), circulation Gamma per core cross-section, domain and boundary conditions, solver timesteps, conservation/accuracy logs, and truly held-out source-provider identity. Previously image-relaxed KnotPlot examples are not qualified physical references.

## Perturbation protocol (preregister before data)

1. Compute an unforced, unperturbed absolute-time Euler trajectory as baseline; demonstrate space/time convergence and energy/helicity/circulation closure.
2. Apply a *zero-net-circulation, divergence-free* finite-bandwidth azimuthal perturbation around the identified core tangent, measured in comoving local frame. Simultaneously construct matched positive-control axial-advective and axis-bending perturbations of comparable perturbation norm.
3. Test a 7-angle scan and 5-k scan as reference initial grid, modifying only if physically inadmissible and declaring this before receipt of blinded truth labels. Explicitly treat theta=0 and theta=90 as boundary cases.
4. Measure spatiotemporal Fourier response, intrinsic omega = omega_lab - k dot U_background, group transport by localized wavepacket energy/perturbation transport, phase speed, residual to linear Euler model, and leakage to Kelvin bending and inertial modes. Do not identify a mode based on swirl phase alone.
5. Assess k-dependence, directionality, polarization/chirality, Galilei-invariant quantities and any dynamic stopping rule. Pre-frozen tolerances should derive from qualified numerical errors, NOT the desired c.
6. Derive independent Swirl Clock f = d tau / dt and physical rod metric A = d ell_op/dx from the same qualified run or independent clock/rod provider. Only afterward compare c_local=(A/f)v_group with c, including different moving observers.
7. Seal observational targets separately (redshift, Shapiro, bending, propagation constraints, SN/BAO/CMB). Do not adjust based on target residuals.

## Restrictions

Do not extrapolate rigid-body rotation to an infinite 3D Euclidean background. Synthetic nondispersive torsion-like pulse is manually inserted, not self-propagating Euler dynamics. A candidate absolute propagation speed is not universally source-dependent; it must be independently determined from background interactions and tested against source-velocity bounds.
