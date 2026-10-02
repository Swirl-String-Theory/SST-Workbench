# CHANGELOG

## v0.2.3

- Added frozen post-confirmatory local-basin diagnostic around revealed G0002 / m=3.
- Added 12 hash-locked paired perturbation directions and seven-amplitude map (72 nonzero trajectories + baseline).
- Added explicit parent-v0.2.2 provenance and non-supersession rule.
- Added core support gate at epsilon 0.00125 and 0.0025 (>=9/12 strict m=3 directions each).
- Added cross-direction frequency robustness gate (CV <=0.20).
- Added conditional modal numerical-convergence check.
- Added resumable trajectory cache and multiprocessing support.
- Removed temporal-memory and Floquet/RPO inference from the v0.2.3 primary scope.
- Added exact-prefix modal persistence optimization: one transverse-mode transform per trajectory, then identical checkpoint prefix reductions; verified against v0.2.2 implementation.
