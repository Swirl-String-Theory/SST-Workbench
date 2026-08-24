# Conclusions

**Verdict:** `MECHANISM_NOT_ESTABLISHED`

- finite-core mode valid fraction: 0.062
- median valid-only measured-delay error: 0.02022
- phase-measurement valid fraction: 1.000
- median phase uncertainty: 0.0001256 rad
- carrier-level closed-loop sign p (both-valid, non-neutral only): 1
- median bounded CLOSED-vs-control growth effect: nan
- phase-effect leave-one-carrier-out CV R²: nan
- grouped phase permutation p: 1

No delay is supplied to the dynamics. v0.1.2 refines the packet return continuously, gates phase by measured numerical/dispersion uncertainty, reports intrinsic frequency, and uses bounded growth response for phase statistics.
