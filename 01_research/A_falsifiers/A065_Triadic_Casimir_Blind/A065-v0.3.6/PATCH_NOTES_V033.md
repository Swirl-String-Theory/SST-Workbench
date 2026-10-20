# A065 v0.3.3 — minimal prerequisite routing patch

Base: archived v0.3.2; frozen framework v1.0.7 external and unchanged.

1. Pre-freeze G3 dependency changes from `[G2]` to `[G1,G10]`. G2 still FAIL on original two coarse 75-point spatial controls; no numerical thresholds, forces or operators were changed.
2. A routing guard additionally requires exact 19-reference-gate legacy signature, G10 PASS, temporal PASS, v0.3.2 precommit unchanged and the 11 protected source/seal hashes unchanged. Any mismatch blocks G3 evaluation.
3. When admitted, G3 is *evaluated but UNRESOLVED*, not PASS. G4/G8 remain not-run; G11 remains independently FAIL or UNRESOLVED.
4. `preregistration/ROUTING_V033.json` is hashed into the pre-freeze official `science_contract.json`. No modifications to frozen framework code or reveal data.
5. Native C++ kernel/solver source is unchanged. GPU profiling is NOT enabled in the official CPU instance.

Status: source package for LOCAL user testing; official Windows v1.0.7 FREEZE/FULL must be run on the user's machine. The packaged release is not a certified physical result.
