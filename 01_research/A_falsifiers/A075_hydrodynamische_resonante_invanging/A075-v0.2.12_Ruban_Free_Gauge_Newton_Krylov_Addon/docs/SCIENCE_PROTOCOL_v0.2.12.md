# A075-v0.2.12 scientific contract

## Equation and search manifold

Let X0 be the SHA256-pinned, interpolated A007 T(2,3) centerline, with local orthonormal normal frame (e1_i,e2_i). Parametrize X_i=X0_i+u_i e1_i+v_i e2_i, with 2N independent unknowns (u_i,v_i). Solve simultaneously for U and Omega in the equation

    P_current_perp[ F_Ruban[X] - U e_z - Omega(e_z x X) ] = 0.

F_Ruban is the regularized Biot-Savart integral plus local binormal curvature in Ruban's nondimensional model. P_current_perp removes the tangent gauge; it is NOT a physical tangential force.

Two independent phase conditions are obtained by QR orthonormalization of the reference normal projections of e_z and e_z x X0. This fixes an *axial* translation and rotation phase. It does not fix arbitrary SE(3) rotation/translation or geometric scale. A local normal chart limits the maximum node displacement.

## Discretization and solver

Use periodic 2pi Fourier derivatives, trapezoidal integral quadrature at the same nodes and constant delta=0.05. Residual unknowns 2N+2, equations 2N normal components + two group phase constraints. Finite difference JVP with GMRES. Use right FFT-based numerical preconditioner and monotone backtracking; do not regularize the physical field. Independent midpoint quadrature is a *post-solve* holdout, not a secretly co-fitted objective.

The stopping tolerance is a *finite discrete nonlinear algebraic* tolerance. It is not an analytic exactness certificate. A full nonlinear and continuum stability claim requires a resolved stationary seed, continuation of physically meaningful operator parameters, spectrum of the properly constrained linearization, and dynamical perturbation validation. The v0.2.11 2N eigenvalue matrices at non-equilibria are not physical stability evidence.

## Weaknesses to disclose

- Fixed-axis screw motion is a restriction; non-axial screw motions are not solved.
- The normal-graph chart can fail for large deformations or bifurcations and is not a global existence solver.
- Static source geometry is analytically reconstructed, not the author's perturbed initial data.
- Spatial and quadrature convergence can fail even if the discrete nonlinear solve appears converged.
- The fast backend is checked for algebraic parity, not certified in all floating-point environments.
- The original A075-v0.2.9 physical Euler finite-core model and Framework v1.1.0 gates are not run or promoted.
- Initial family is only torus T(2,3), B0=77/500; transfer to other embeddings is not yet supported.
- This study does not prove Ruban's original long-lived trajectory or spectral stability.

## Required follow-up

Increase resolved N while assessing midpoint/trapezoid trends; run independent deformation manifold and parameterization checks; compare finite-difference Jacobian-vector derivatives; prove/measure stability only after normal residual is physically and numerically closed. Preserve nonzero/unresolved gate status when checks fail.
