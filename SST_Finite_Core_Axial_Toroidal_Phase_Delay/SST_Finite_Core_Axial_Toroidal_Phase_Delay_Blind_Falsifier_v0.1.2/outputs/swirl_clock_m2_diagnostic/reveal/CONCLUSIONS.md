# Conclusions

**Verdict:** `M2_PHASE_DIAGNOSTIC_INCOMPLETE`

- finite-core mode valid fraction: 0.354
- median valid-only measured-delay error: 0.01615
- phase-measurement valid fraction: 0.824
- median phase uncertainty: 0.01054 rad
- carrier-level closed-loop sign p (both-valid, non-neutral only): 0.6875
- median bounded CLOSED-vs-control growth effect: 0.01148
- phase-effect leave-one-carrier-out CV R²: -0.4027
- grouped phase permutation p: 0.366
- discovery regime: m=2, OTHER_BRANCH
- discovery phase minimum: 1.8426 rad
- discovery bootstrap circular SD: 0.4508 rad
- this phase is **discovery only** and must be frozen in a later independent release before confirmation.

No delay is supplied to the dynamics. v0.1.2 refines the packet return continuously, gates phase by measured numerical/dispersion uncertainty, reports intrinsic frequency, and uses bounded growth response for phase statistics.
