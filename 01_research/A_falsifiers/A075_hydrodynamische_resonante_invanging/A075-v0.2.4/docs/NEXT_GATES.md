# A075-v0.2.2 — Exact release stop criteria

STOP on any A021/A032 hash mismatch, invalid framework version, source XYZ missing, nonfinite output, or invalid CFL. Abort physical interpretation if period counts are unavailable, donor exit not proven, there is no time window after departure, the receiver leaves the ROI, remeshing/artificial diffusion dominates, or global/local energy budgets fail convergence.

Qualification requires a physical fixed final time across all grids and dt refinements; core Gaussian width fixed physically for spatial tests; independent core-width/profile sensitivity; box size independence; temporal refinement at fixed spatial grid; third refinement level for Richardson trends; surface/window width convergence; shape deformation, helicity, circulation, and topology verification; an independent receiver-only clock with at least 100 post-exit cycles; and a provenance-clean held-out knot family.

The `PREVIEW` generated in this package is an explicitly **underresolved smoke run**, not a physical G2 pass. Temporal and spatial response comparisons that look small are insufficient if `core/dx < 4` in BASIC/FULL. Positive initial or late window excess is expected while the incoming donor is still in range and is not evidence of trapped energy.

The verified exact-source SHA256 commitments from v0.1.0 for A021/A032 are retained unchanged. Other source files and knot bytes are independently hashed on input.


## v0.2.2 spacing/timestep update
BASIC: N=80/112, a=0.50, dt=0.015/0.0075, T=1.2; FULL: N=96/128, a=0.50, dt=0.010/0.005, T=9.0; ALL runs fixed T within spatial/temporal ladders. `max_CFL<0.20`; minimum initial core sigma/dx >=4 for screening. Small drift is insufficient: monitor error in late window energy, pressure flux, effective vorticity core width, Fourier cutoff sensitivity, periodic images. Third spatial resolution and core-profile variations remain mandatory before G2 physics qualification.
