# Method: finite-core eigenmodes and emergent loop delay

## 1. Scope

This package is a **slender finite-core linear Euler mechanism falsifier**. It is not a full 3-D Euler DNS and does not claim that a local columnar eigenmode is by itself a complete knotted-vortex equilibrium.

The local base flow in core-radius coordinates is

\[
\mathbf V_0(r)=V_\theta(r)\,\mathbf e_\theta+U_s(r)\,\mathbf e_s,
\]

with both axial and toroidal vorticity when \(U_s'(r)\ne0\). Three smooth finite-core profile families are tested.

Perturbations are normal modes

\[
\delta q(r,\theta,s,t)=\hat q(r)e^{i(m\theta+ks)+\lambda t}.
\]

The primitive-variable generalized eigenproblem is the discretized linearized incompressible Euler system

\[
(\lambda+i\Omega_D)u_r-\frac{2V_\theta}{r}u_\theta=-p',
\]
\[
(\lambda+i\Omega_D)u_\theta+\left(V_\theta'+\frac{V_\theta}{r}\right)u_r=-\frac{im}{r}p,
\]
\[
(\lambda+i\Omega_D)u_s+U_s'u_r=-ikp,
\]
\[
\frac1r(r u_r)'+\frac{im}{r}u_\theta+iku_s=0,
\]

where \(\Omega_D=mV_\theta/r+kU_s\).

## 2. Closed knotted carrier

The carrier is represented by a closed centerline only to supply global slender-tube geometry. The finite core itself is solved radially. The code measures carrier length \(L\), curvature, and the parallel-transport (Bishop) holonomy \(\Theta_B\).

The closed-loop mode condition is

\[
\boxed{k_{mn}a=\frac{2\pi n-m\Theta_B}{L/a}}.
\]

The null changes this to a preregistered non-integer offset \(n\to n+\delta\), with the sign of \(\delta\) randomized before blinding.

## 3. Delay is measured, never supplied

For each selected finite-core hybrid mode the same eigenbranch is followed at nearby wavenumbers. A polynomial fit to \(\omega(k)\) gives

\[
v_g=\frac{d\omega}{dk},\qquad \tau_g=\frac{L}{|v_g|}.
\]

A narrow wave packet is then propagated on the periodic loop using that **measured dispersion curve**. The code independently measures its first return time \(\tau_{ret}\). No `tau_delay`, `feedback_delay`, target phase, damping controller, or user-selected return phase exists in the dynamics.

The return phase is measured as

\[
\phi_{loop}=\arg A(0,\tau_{ret})-\omega_0\tau_{ret}\pmod{2\pi}.
\]

## 4. Primary gates

1. **FC1 finite-core mode gate:** a localized mixed axial/toroidal eigenmode exists and survives radial-resolution checks.
2. **FC2 emergent-delay gate:** wave-packet return agrees with \(L/|v_g|\) within the preregistered tolerance.
3. **FC3 closed-loop spectral gate:** the geometrically closed condition has lower converged growth than the non-integer closure control at carrier-cluster level.
4. **FC4 phase-predictive gate:** without specifying a preferred phase, leave-one-carrier-out circular regression tests whether measured \(\phi_{loop}\) predicts spectral growth. A preregistered permutation test controls the false-positive rate.

A strong mechanism verdict requires all four.

## 5. Validity limits

The local operator is a straight-column finite-core Euler problem. Carrier curvature enters through a **slender-core validity gate** and through closed-loop geometry/holonomy, not through the full curved-tube Euler operator. Therefore a positive result motivates a second-generation curved-tube calculation; it is not itself proof of nonlinear orbital stability.
