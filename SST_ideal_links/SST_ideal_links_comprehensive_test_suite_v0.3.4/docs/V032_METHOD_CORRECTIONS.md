# v0.3.2 method corrections

1. Pairwise Gauss linking is evaluated on a grid independent of the reduced Hessian grid.
2. Pairwise-zero does not mean unlink: all two- and three-component pairwise-zero links are flagged.
3. Candidate component automorphisms are not used to identify circulation sectors.
4. Fixed reference scales replace per-sector division by potentially tiny baselines.
5. The cancellation ratio `||sum w_i g_i|| / sum ||w_i g_i||` measures closure fine tuning.
6. Diagonal Hessians cannot establish positive semidefiniteness or spectral stability.
7. Full/max presets compare the primary gradient/Hessian under step halving.
