# Method — v0.1.2

## 1. Finite-core local eigenproblem

The base flow is

\[
\mathbf V_0=U_s(r)\mathbf e_s+V_\theta(r)\mathbf e_\theta,
\]

and perturbations are solved with a Chebyshev-collocated linearized incompressible Euler generalized eigenproblem.

## 2. Closed carrier geometry

The carrier supplies loop length, curvature validity and Bishop-frame holonomy.  Exact loop closure obeys

\[
kL+m\Theta_B=2\pi n.
\]

## 3. Symmetric closure control

The control averages `k0-dk` and `k0+dk`, cancelling first-order dispersion-slope bias.

## 4. Axial-flow branch continuation

When enabled, the mode is selected at a preregistered axial-flow anchor and transported to the target `U_s/V_theta` by eigenvector overlap.  Loss of overlap invalidates the branch instead of allowing an implicit branch jump.

## 5. Self-generated group delay

The tracked local dispersion relation gives `v_g=domega/dk` and the predicted loop delay.  No delay appears in the eigenproblem.

## 6. Continuous return and phase measurement

A coarse packet-envelope scan brackets the first loop return.  Bounded continuous optimization refines the maximum.  A second tighter optimization estimates return-time numerical uncertainty.  The local refinement tolerance is tied to a maximum phase advance, rather than using a fixed global number of time samples.

The absolute phase is accepted only when uncertainty from both return timing and dispersion-frequency fit remains below the preregistered threshold.

## 7. Lab and intrinsic clocks

For each mode the code reports both lab-frame `omega=-Im(lambda)` and

\[
\omega_{intrinsic}=\omega-\langle mV_\theta/r+kU_s\rangle_E.
\]

This avoids interpreting simple Doppler/advection as an internal clock shift.

## 8. Phase-growth statistics

Phase fits use the bounded effect

\[
E_g=(g_C-g_S)/( |g_C|+|g_S|+2g_0),
\]

not the singular log ratio.  Only both-valid, non-neutral and phase-valid rows are eligible.

## 9. Discovery versus confirmation

v0.1.2 may discover a new phase minimum after correcting the observable.  It may not call that minimum confirmed.  A separate later release must freeze it before new data.
