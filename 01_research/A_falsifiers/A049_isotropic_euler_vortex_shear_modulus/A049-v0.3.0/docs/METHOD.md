# Method — v0.3.0

The candidate microstructure is a low-discrepancy SO(3) ensemble of Hopf-linked circular filament pairs. Each cell is dynamically independent in this release; ensemble averaging supplies the coarse-grained isotropic response.

The filament Hamiltonian is evaluated with a finite-core Rosenhead-type regularization. Node motion uses the matching regularized Biot–Savart velocity and RK4. No reconnection operation exists in the solver.

Static stiffness is obtained from even-in-shear energy curvature. Dynamic persistence is tested in two ways: repeated modulus measurements on the evolving unsheared cell, and an independent +gamma/-gamma shear-relaxation experiment whose odd macroscopic stress is measured by a small virtual-shear derivative.

Numerical qualification includes link-number controls, unlinked control, orientation isotropy, energy drift, RK4 local convergence, exact objectivity of the energy kernel, filament-node resolution, and forward/backward reversibility.
