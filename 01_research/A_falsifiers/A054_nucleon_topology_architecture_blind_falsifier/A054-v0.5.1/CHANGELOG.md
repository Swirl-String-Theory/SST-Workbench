# Changelog

## v0.5.1

Numerical/variational consistency patch after the frozen v0.5.0 FULL diagnostic.

- Replaced the raw-gradient/post-projection mismatch with one canonical constrained objective `U_c = H(N[R(X+deltaX(q))])`.
- Gradient, Armijo acceptance, stationarity, Hessian, and ringdown now use the same objective.
- Added global Armijo/trust-region controls and deeper backtracking; no topology/provider-specific retuning.
- Added explicit `UNRESOLVED_NUMERICAL` carrier status when constrained-objective descent cannot be demonstrated.
- Gate fractions now use lower/upper bounds so unresolved numerical cases are not silently counted as scientific failures.
- Added Hessian finite-difference sweep at `eps`, `eps/2`, `eps/4`; stability sign is authoritative only after convergence.
- Preserved v0.5.0 provider/topology scientific thresholds and E013 carrier authority.
- Bumped all output/handoff authority strings to v0.5.1.

v0.5.0 remains frozen historical evidence and is not modified by this patch.
