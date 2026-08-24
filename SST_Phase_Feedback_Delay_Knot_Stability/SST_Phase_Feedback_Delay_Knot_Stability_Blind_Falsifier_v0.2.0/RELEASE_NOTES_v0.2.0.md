# v0.2.0

- deduplicates exact canonical geometries before blinding/statistics;
- excludes the 10 v0.1.7 canonical geometries from prospective confirmatory runs;
- hash-grouped train/holdout with no geometry leakage;
- independently measures loop delay with localized Kelvin packet transport;
- uses dimensionless nonlinear growth `Sigma = sigma_obs * tchar`;
- replaces the v0.1.7 absolute `sigma0+kappa z` gate with frozen constrained negative-slope holdout;
- locks preregistration/config/reference hashes;
- adds retrospective legacy-audit mode and orthogonal preparation endpoint audit.

- freezes `basic` as the sole primary confirmatory endpoint; `extended` is robustness-only.
