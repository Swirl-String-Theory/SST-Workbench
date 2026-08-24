# Conclusions

**Verdict:** `M1_PHASE_DISCOVERY_INCOMPLETE`

- finite-core mode valid fraction: 0.417
- median valid-only measured-delay error: 0.09729
- phase-measurement valid fraction: 0.875
- median phase uncertainty: 0.005038 rad
- carrier-level closed-loop sign p (both-valid, non-neutral only): 0.875
- median bounded CLOSED-vs-control growth effect: 0.0008244
- phase-effect leave-one-carrier-out CV R²: -0.04766
- grouped phase permutation p: 0.157
- discovery regime: m=1, FAST_SWIRL_LOCKED
- discovery phase minimum: 4.2813 rad
- discovery bootstrap circular SD: 1.368 rad
- this phase is **discovery only** and must be frozen in a later independent release before confirmation.

No delay is supplied to the dynamics. v0.1.2 refines the packet return continuously, gates phase by measured numerical/dispersion uncertainty, reports intrinsic frequency, and uses bounded growth response for phase statistics.
