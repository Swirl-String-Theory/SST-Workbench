# VALIDATION

Artifact-environment checks:

- Design selftest: PASS.
- Geometry lock: K31 / `load 3.1` only.
- 20 new configurations: PASS.
- Lane split: 12 joint-ray + 8 hooke-bracket.
- Preregistration lock: PASS.
- Generated KPCs: 20/20.
- Static KPC syntax: PASS 20/20.
- Every run contains 10 checkpoints:
  `0,10,25,50,100,250,500,1000,4000,10000`.
- Runtime parameters use `name = value` assignment syntax.
- All non-q/h/p assignments are copied from v0.1.0.
- No T(2,3) script exists in this release.

Scientific guardrail:

A sign reversal in the early geometric observable identifies an operational
expansion/contraction zero bracket. Restoring stability still requires a later
geometry-perturbation test.
