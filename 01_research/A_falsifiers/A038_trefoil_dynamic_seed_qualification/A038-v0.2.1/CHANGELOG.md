# Changelog

## v0.2.1 — scientific correctness and evidence sealing

- Audits and locks the actual v0.2.0 BASIC interpretation: one accepted source family, 0/8 S37, no S40–S60 physics result.
- Uses full-name trefoil/knot discovery, rejects `link_*`, checks closed-curve sampling and requires three accepted source groups for scientific profiles.
- Separates sealed blind material from public outputs and writes a pre-scoring evidence manifest with code/config/dataset/threshold hashes.
- Adds direct N-to-N trajectory/final-shape convergence and explicit temporal `FLOOR_LIMITED` / `ORDER_CONFIRMED` / `FAILED` states.
- Fixes the zero-S37 chain-verdict precedence bug.
- Requires the return itself to occur after the observation minimum and gates local mesh/contact state at that return.
- Freezes a shared S40/S50 dynamics contract; projected Floquet now differentiates that same map and removes resolved neutral directions.
- Recasts S60 as held-out predictive specificity. Causal claims remain unauthorized without intervention or ablation.
- Adds a four-source workflow-smoke profile whose physics verdict is always not-applicable.
- Requires family/provenance declarations for scientific promotion; three files from one family cannot satisfy diversity.
- Commits identity/source/refinement/evidence maps, redacts public source names, and makes reveal fail closed on tampering.
- Freezes the actual S40 timestep/guard cadence for every S50 perturbation, compares spatial trajectories at equal times, and rejects unrealized temporal ladders.
- Adds an executable native selftest entry point and expands the test suite to 40 tests.

## v0.2.0 — source-stratified dynamic-shape search and numerical-certification redesign

### Scientific design
- Reframes the primary target as finding the trefoil start shape that most naturally enters coherent rolling/free motion before testing downstream mechanisms.
- Makes low-dimensional POD/QHP structure diagnostic-only; it no longer improves seed score.
- Adds champion-cluster semantics so a ~10^-3 score difference cannot be overclaimed as a unique winner.

### S10 / S20 / S25
- Geometry-aware source dedup after cyclic/rigid alignment.
- Round-robin source-stratified candidate scheduling and source-group-aware promotion/refinement.
- Preserves hidden provenance until S70.

### S30 / S32 / S35
- Retains explicit spatial N-ladder.
- Adds S32 fixed-N timestep ladder with floor-aware RK4 convergence certification.
- S35 reports champion cluster + optional unique champion only after a frozen margin.

### S37 / S40
- Replaces the old long-run target-projection mesh controller by direct segment-length-feedback tangential velocity.
- Adds RMS mesh-speed cap relative to physical Biot-Savart RMS speed.
- Makes shape comparisons parameterization-invariant via uniform-arclength resampling + cyclic + rigid alignment.
- Adds S37 low/nominal/high mesh-gauge certification.
- S40 always emits a complete recurrence/status schema and separates numerical coverage from physics no-RPO.
- A certified early return can remain RPO-eligible even if the trajectory later stops, provided local return gates pass; global hard FAIL still requires preregistered coverage.

### S50 / S60
- S50 respects S37/S40 eligibility and reports NOT_RUN/INDETERMINATE when long-run numerics are insufficient.
- S60 now requires material-core held-out improvement **and** a material-over-fixed null advantage.
- Measured phase remains diagnostic-only; no target phase/delay is supplied.

### Regression/validation
- Adds five v0.1.1 champion geometries as numerical regression fixtures.
- R557 regression now reaches T=1.2 under nominal mesh control where v0.1.1 stopped around T=0.768.
- Native↔Python relative L2 parity `2.898329577875693e-17` in generation validation.
- Pytest suite expanded to 14 tests before final packaging.
- Adds cross-campaign methodology notes and disables unsafe v0.1.x `run_resume_from_50.cmd` path.
