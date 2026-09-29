# v0.3.x roadmap

v0.3.0 is the E010-v0.3.1 source-native carrier integration release.

Next numerical tranche after a clean population screen:

1. add velocity-gradient tensor M=grad(u) and strain eigenframe histories at the vorticity hotspot;
2. add pressure-Hessian H=grad grad p and Lagrangian deformation-gradient F diagnostics;
3. check F_t=M F and F_tt=-H F residuals along selected trajectories;
4. escalate only suspicious carriers to N=32/48/64 and timestep refinement;
5. compare pure Euler evolution to a matched finite-core SST regularization without mixing the two gates.
