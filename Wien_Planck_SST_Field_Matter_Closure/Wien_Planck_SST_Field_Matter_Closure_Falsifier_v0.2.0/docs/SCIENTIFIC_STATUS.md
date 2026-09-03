# Scientific status of v0.2.0

## Implemented end-to-end from raw centerlines
- source/canonical geometry hashes;
- multi-component parsing and uniform resampling;
- regularized Biot--Savart C++/Python kernels;
- best-rigid-motion relative-equilibrium residual;
- adaptive RK4 with current-spacing \(\Delta t\propto\Delta s^2\);
- exact-time arclength redistribution;
- matched \(+\epsilon/-\epsilon\) broadband probes;
- discovery-only POD basis and frozen holdout projection;
- h-free line-energy extraction using \(\rho_{\!f}\);
- temporal and spatial convergence diagnostics;
- blind universal-action gates including the classical continuous-amplitude null;
- private reveal-key commitment and target comparison only after blind scoring.

## Analyzer available, but requires independent observables
The broader Wien--Planck field--matter gates for \(M_E/M_I\), pressure monopole \(C_p/M_I\), and coarse-grained \(\beta_{\rm knot}/\beta_{\rm fluid}\) are implemented as an external-observable analyzer. v0.2.0 does **not** fabricate these observables from a line-filament model.

## Not claimed
- independent topology certification;
- full 3-D finite-core incompressible Euler DNS;
- reconnection physics;
- microscopic entropy production;
- true Floquet monodromy without a closed relative-periodic orbit;
- a Planck-scale prediction from the provenance identity.
