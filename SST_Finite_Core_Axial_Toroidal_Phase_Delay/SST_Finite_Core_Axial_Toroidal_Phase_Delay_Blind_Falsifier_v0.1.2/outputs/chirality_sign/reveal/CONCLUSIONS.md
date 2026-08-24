# Conclusions

**Verdict:** `MECHANISM_NOT_ESTABLISHED`

- finite-core mode valid fraction: 0.617
- median valid-only measured-delay error: 0.1877
- phase-measurement valid fraction: 0.622
- median phase uncertainty: 0.0503 rad
- carrier-level closed-loop sign p (both-valid, non-neutral only): 1
- median bounded CLOSED-vs-control growth effect: 0.00185
- phase-effect leave-one-carrier-out CV R²: -0.595
- grouped phase permutation p: 0.626

No delay is supplied to the dynamics. v0.1.2 refines the packet return continuously, gates phase by measured numerical/dispersion uncertainty, reports intrinsic frequency, and uses bounded growth response for phase statistics.
