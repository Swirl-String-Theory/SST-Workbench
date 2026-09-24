# A043 roadmap — v0.2.0

Priority upgrades:

1. ingest PKLSA, KAtlas, KnotPlot, Fourier-series and ideal/Ridgerunner trefoil centerlines through a single provenance-aware source adapter;
2. replace the current strain-aligned packet proxy with transported phase/amplitude ODE diagnostics based on the high-frequency Euler system used in the 2026 amplification construction;
3. add Lagrangian deformation gradient `F`, velocity-gradient tensor `M`, and pressure-Hessian `H` tracking, including checks of `F_t = M F` and `F_tt = -H F`;
4. run frozen spatial ladders at least N=48/64/96 for surviving seeds and explicit dt-halving at each decisive resolution;
5. add CFL-controlled integration, checkpoint/resume, and fail-closed under-resolution guards;
6. add a finite-core branch to test whether continuum amplification saturates at a prescribed core scale, keeping canonical SST constants reveal-only;
7. emit an A038-consumable P0 certificate so Trefoil Dynamic Seed Qualification rejects seeds with unresolved or convergent BKM-warning signatures before expensive Floquet stages.
