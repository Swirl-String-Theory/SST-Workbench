# Scientific protocol

## Primary hypotheses

**H1 — Dynamic seed existence.** There exists a trefoil geometry in the preregistered local shape family whose early free dynamics is dominated by coherent rigid/rolling motion rather than intrinsic normal deformation.

**H1b — Local refinement.** A preregistered adaptive neighborhood around top anonymous seeds can improve rolling quality without revealing source identity.

**H2 — Resolution robustness.** Seed quality persists across the fixed spatial ladder.

**H2b — Core-radius robustness.** Seed ranking is not a narrow artifact of one regularized core fraction.

**H3 — Orbital recurrence.** A qualified seed exhibits nontrivial repeated symmetry-reduced returns.

**H4 — Projected linear stability.** A near-RPO has projected nontrivial Floquet spectral radius within the frozen tolerance.

**H5 — Finite-core clock mechanism.** On an H4 candidate, a self-generated material-core stretch delay improves held-out prediction of modal acceleration while the fixed-core null does not.

## Anti-overfitting rules

1. Identity and deformation parameters remain sealed during S20–S60.
2. S20 score weights are fixed in config before preparation.
3. S25 may optimize only around anonymous S20 parents using frozen ranges.
4. S30 tests the combined frozen S20/S25 ranking; later stages cannot nominate a new seed.
5. S35 only tests S30-qualified candidates across a frozen core-radius ladder.
6. S40 only tests S35-qualified candidates.
7. S50 only tests S40 near-return candidates.
8. S60 only tests S50 projected-Floquet candidates.
7. Discovery delay in S60 uses only the first half of the trajectory.
8. No target phase, preferred period or per-candidate fit parameter enters the dynamics.
9. No silent timestep coarsening: `dt ~ ds^2` failure aborts.
10. A numerical PASS is never labelled a physical SST proof.

## Recommended use

Use BASIC to validate the pipeline and get a first seed ranking. Use EXTENDED for scientific comparisons. Use PRODUCTION only after the parameter ranges and thresholds have been frozen in a git commit / SHA256 manifest.

## S40 → S50 stage-boundary contract (v0.1.1)

A long-run row is eligible for projected RPO/Floquet analysis only when all of the following are true:

1. the long run completed;
2. `best_return` is finite and no larger than the preregistered loose-return threshold;
3. `best_return_time` is finite and positive;
4. `max_mesh_ratio` is finite and no larger than `long_max_mesh_ratio`.

Non-finite S40 sentinels are serialized as JSON `null`; S50 therefore validates the schema explicitly and rejects such rows fail-closed. S50 may not reconstruct a broader pool than S40.
