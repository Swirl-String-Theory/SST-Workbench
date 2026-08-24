# Preregistration — v0.4.7 HR DD32 ladder

The machine-readable preregistration is `configs/hr_ladder/ladder_plan.json` plus the six rung JSON files in the same directory.

The following are fixed before unblinding the ladder synthesis:

1. spatial rungs: (N,k_max)=(360,8),(540,8),(720,8);
2. spectral rungs: (720,8),(720,12),(720,16);
3. P1 epsilon set: {0.001,0.002,0.004,0.008};
4. reference Jacobian epsilon: 0.004;
5. finite-amplitude robustness epsilons: {0.012,0.016}, R5 only;
6. normalized-growth threshold: 0.12;
7. tail contraction ratio maximum: 0.85;
8. relative last-step maximum: 0.05 for both spatial and spectral tails;
9. dominant k_max eigenvector-weight maximum: 0.15;
10. CPU-FP64 near-threshold margin: |g-0.12| <= 0.02;
11. diagnostic power exponent scan: 0.25 <= p <= 4.0;
12. R0–R4 disable dynamics; R5 retains the FULL ringdown/RPO/Floquet settings inherited from archive_full.

No extrapolated value is allowed to override an uncontracted or non-quasi-monotone measured tail.
