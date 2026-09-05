# Release notes — v0.4.3

v0.4.3 closes the reporting ambiguities found after the successful v0.4.2 native campaign. The Biot--Savart operator, analytic Jacobian, Rosenhead regularization, stationary equation, and convergence thresholds are unchanged.

## Corrections

- Explicit clock-boundary brackets and connected real-clock components per sampled ray.
- Separate counts for any-valid and fully-valid rays.
- Separate candidate fractions normalized by valid rays, all rays, and fully-valid rays.
- Censored or bracketed bifurcation thresholds instead of the ambiguous `epsilon_loss_sampled` field.
- Regression coverage for the split-domain control scan at `epsilon/r_c=0.0010`.

## Status

This release still resolves local stationary Fermat candidates only. It does not integrate a complete closed ray and cannot certify a QSM pole.
