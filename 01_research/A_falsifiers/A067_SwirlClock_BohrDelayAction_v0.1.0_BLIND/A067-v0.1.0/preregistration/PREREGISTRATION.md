# SST-SC-BDA v0.1.0 — preregistration (development-control tranche)

**Frozen science objective (proposal; before qualified PKLSA registration):** In the absolute background time T of a 3D incompressible inviscid Euler fluid, test whether a *carrier-resolved*, material, periodic vortex field supplies (i) an operational local clock, (ii) an independently derived delayed phase-feedback closure with stable discrete frequencies, and (iii) an independently derived canonical action ladder with an approximately universal action increment. The stages are separate and non-substitutable.

**Null H0:** Observed harmonicity/phase locking is produced by kinematic closure, projection, selected fitting, or a reduced delayed oscillator not derived from physical Euler flow. Even where frequencies are discrete, the action can vary continuously with inertia and/or amplitude and no physical universal action increment or local clock is established.

**Alternative H1, falsifiable conditional prediction:** Across >=2 independently qualified dynamic 3D sources and >=3 stable adjacent modes per family, blinded preregistered extraction of actual canonical actions has a common increment within 5% after propagated numerical error <=1% and without any target constant in discovery, and each accepted carrier supports a reproducible local clock mapping d tau_clock/dT. The corresponding feedback delay and coupling must be measured from the same parent 3D dynamical solver, not freely fitted.

**Important: v0.1.0 is a methodological / synthetic-controls version.** No real PKLSA trajectory, canonical 3D momentum, or time-rate observable is yet available and scientific G7-G9 remain unresolved. No science reveal is permitted.

## Physical definition of Swirl Clock

For carrier K, choose *before looking at outcomes* a scalar or complex intrinsic cyclic readout z_K(T) calculated from the fully resolved 3D fluid (not from a drawing of the knot). Extract a continuous unwrapped phase phi_K(T) only when |z_K| exceeds a preregistered signal floor. Define a *clock indication* tau_K(T)=phi_K(T)/omega_ref,K, where omega_ref,K is a fixed, independently calibrated reference angular rate, and local rate S_K(T)=d tau_K/dT. Absolute time T is the common Euler evolution parameter. Differences between two clocks are ratios of measured S_K. This does not assert relativistic time dilation or define omega_ref from the measured target.

## Required data schema for qualified real source

- Named project/provider and independent provider evidence class; exact SHA256 of source; source revision, temperature/solver/model details.
- Full 3D Euler u(x,T) or eligible material Lagrangian time trajectories with enough information to reconstruct phase, circulation and transport; NOT a static mesh, snapshot diagnostic, projection, fitted phase-only DDE or generic metadata.
- At least 3 finite spatial resolutions and 3 time steps at fixed final physical time with energy/helicity/divergence error budgets; sufficient sample duration (>100 local periods).
- Independent mechanism for phase-return delay tau_K (signal transit), not automatically tau=L/v_swirl; signal characteristic speed must be measured.
- Explicit symplectic/reduced Hamiltonian or canonical momentum and an action integral on periodic/recurrent orbit. Action must be invariant under smooth reparameterization and gauge changes when applicable.

## Gate rules (always run all diagnostic gates; no fail-early suppression)

| Gate | Qualification | Decision rule |
|---|---|---|
| G0 | SHA256 commitments and source provenance | any hash mismatch FAIL; synthetic evidence cannot become independent |
| G1 | Harmonic Fourier analytic reference | abs(relative action integration error) < 1e-10 |
| G2 | SST-60 exact locking roots and sufficient stability | root residual < 1e-9 in dimensionless theta; stable A>0 and unstable A*tau<-1 classification |
| G3 | Delay-method-of-steps time-domain calibration | abs(theta_measured-theta_exact) < 0.015 at two dt values; screening only |
| G4 | Rotor angular action algebraic check | action spacing CV < 0.25 in developmental finite-coupling control; NOT an h hypothesis |
| G5 | Harmonic-amplitude negative control | synthetic amplitude variation causes measurable action-gap departure beyond corresponding rotor control |
| G6 | Euler velocity-time scaling null | rescaled action follows continuous factor lambda within 1e-12; diagnostic proof the action is NOT discrete from Euler alone |
| G7 | Actual 3D phase, return delay and clock | HOLD unless certified 3D time-dependent data available + convergence and independent phase readout |
| G8 | Actual canonical momentum and J integral | HOLD unless symplectic projection and 3-resolution convergence <1% demonstrated |
| G9 | Cross-provider action increment and local-clock prediction | HOLD unless G7 and G8 qualified on >=2 independent sources and 3 adjacent modes; only then allow target comparison |

**Negative-control requirement:** If both stable roots and a continuously variable harmonic amplitude are present, the action-closure gate must fail or be withheld. A model yielding a positive action-quantization claim anyway fails.

**Claims not tested in v0.1.0:** fermionic half-integer spin, Born rule, Hilbert space or commutators, quantum phase universality, vacuum gravity, E=mc^2, or causality speed c. A single discrete spectrum does not imply these.

**Registry stance:** this is an A059-adjacent *candidate add-on*, not a new registered A-ID. Before production freeze determine whether to use a new A059 version or a new registered project ID; never overwrite A059 v0.2.0.
