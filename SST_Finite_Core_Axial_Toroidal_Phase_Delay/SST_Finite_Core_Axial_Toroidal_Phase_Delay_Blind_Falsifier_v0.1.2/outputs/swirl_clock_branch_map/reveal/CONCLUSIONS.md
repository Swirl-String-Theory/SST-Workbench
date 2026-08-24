# Conclusions

**Verdict:** `MECHANISM_NOT_ESTABLISHED`

- finite-core mode valid fraction: 0.347
- median valid-only measured-delay error: 0.08407
- phase-measurement valid fraction: 0.800
- median phase uncertainty: 0.001767 rad
- carrier-level closed-loop sign p (both-valid, non-neutral only): 0.6875
- median bounded CLOSED-vs-control growth effect: 0.004886
- phase-effect leave-one-carrier-out CV R²: nan
- grouped phase permutation p: 1

No delay is supplied to the dynamics. v0.1.2 refines the packet return continuously, gates phase by measured numerical/dispersion uncertainty, reports intrinsic frequency, and uses bounded growth response for phase statistics.
