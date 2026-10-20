# A069 v0.1.0 scientific preregistration DRAFT

## Top-level gate discipline

G0 protocol integrity (official framework only). G1 legacy-exclusion policy. G2 exact Euler/Kelvin analytic control. G3 independent Cartesian tracer phase in D1. G4 qualified finite-core 3D dynamics. G5 material, mesh-gauge-independent internal phase. G6 E010/E011 source/physical provenance. G7 frozen source-free rate prediction. G8 continuum/time/core pressure-projection, kinetic energy and helicity. G9 independent held-out providers. G10 real C++ FP64 native certification. G11 A061 scientific handoff. G4-G11 remain UNRESOLVED in this D1 tranche, and no scientific FAIL blocks independent downstream *diagnostic* execution.

## D1 analytic exact 3D incompressible Euler benchmark

Let `a` be constant and `Omega(t) = Omega0 exp(a*t)`, and define affine velocity `u(x,t)=M(t)x`, with

    M = [[-a/2, -Omega, 0], [Omega, -a/2, 0], [0, 0, a]].

`tr M=0`; the vorticity is `(0,0,2 Omega)` and `D omega / Dt = (omega . grad)u` has nonzero vortex stretching. Define pressure Hessian `grad grad p = -rho sym(Mdot+M^2)`. For `Omegadot=a Omega`, the antisymmetric part of `Mdot+M^2` vanishes, so the Euler acceleration balances pressure exactly. For a material circular loop `R(t)=R0 exp(-a t/2)`:

    Gamma=2*pi*R(t)^2*Omega(t)=const;
    theta_pred(t)=Omega0*expm1(a*t)/a (continuous for a=0).

In D1 `theta_measured` is extracted from a Cartesian Lagrangian tracer numerically integrated under the velocity field. This checks the code's *phase integration*, NOT existence of an independent vortex particle clock. It is an unbounded affine flow with infinite energy; no finite-core topology or physical SST interpretation is allowed.

## D2-D3 required before physics verdict

D2: 3D incompressible Euler finite-core solution, no arbitrary fit, pressure projection or volume solve, 3 spatial refinements, >=3 time steps each at the same physical final time, two independent integrators, energy/helicity/circulation/divergence/mesh-gauge diagnostics, core radius sensitivity, material-phase coherence, negative controls for rigid translation and arbitrary tangential resampling. Phase must track actual physically advected markers or a derived gauge-invariant mode, never an algorithmic mesh velocity.

D3: E011 STATIC_READY eligible seeds under E010-v0.3.1 provenance; require exact raw and geometry SHA-256 and at least 2 truly independent provider families for general prediction. Trefoil `3_1` primary; `5_1` and `5_2` follow-up only if DYNAMICS_READY; knots must not be promoted from mere E011 static clearance. For D3 controls, non-ready links/visual artifacts are not allowed as *positive* evidence.

Split discoveries and confirmation by provider family, never by resolutions/rotated duplicates. Freeze prediction file (equation, sign, units, uncertainty, source digests) before opening held-out material-phase time series. No use of target time dilation, nuclear clock frequencies, Compton frequency, or A061 experimental outcomes as fitting targets.

## Epistemic status

PASS G2/G3 = verified exact analytic Euler and integrator. PASS G4/G5/G6/G7/G8/G9 = potentially qualifies a dynamical vortex phase prediction *inside the chosen continuum solver*, not observed spacetime dilation. A061 experimental comparisons are a downstream, distinct gate.
