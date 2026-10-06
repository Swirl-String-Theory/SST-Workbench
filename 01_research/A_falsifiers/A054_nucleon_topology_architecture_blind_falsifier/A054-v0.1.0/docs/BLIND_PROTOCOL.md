# Blind protocol v0.1.0

The blind phase receives only anonymous geometry arrays, fixed numerical settings and the anonymous circulation sectors `Q0`--`Q7`. `tools/build_blind_runner.py` exports an allow-listed evaluator that excludes prepare/reveal modules and semantic generator names; its leak scan and source hashes are committed in `RUNNER_MANIFEST.json`.
It must not read `_private/`, source names, topology labels, particle labels, PKLSA provider names, nucleon masses, charge labels, atomic observables or SST canonical constants.

Prepare commits the private map by SHA-256. Blind then seals the manifest, result ledger, analysis and report. Reveal verifies both seals before attaching identity. Reveal **never recomputes** scientific observables.

The geometry itself can in principle be visually reverse-engineered by a human. Thus the package claims code-level/operational blinding, not impossible-to-break cryptographic blinding against a researcher deliberately inspecting anonymous coordinates.

## Status semantics

- `SURVIVES_BLIND_SCREEN`: all mandatory v0.1 numerical/dynamical gates passed.
- `FAIL_DYNAMICAL_CONFINEMENT`: qualified dynamics exceed the frozen shape-drift gate.
- `FAIL_TOPOLOGY_PRESERVATION`: qualified evolution changes pairwise linking beyond tolerance.
- `INCONCLUSIVE_NUMERICAL`: convergence, objectivity or finite integration failed. This is **not** a physical failure.
- `PREPARED_PARTIAL_FAIL_CLOSED`: only analytic controls could be prepared; no nucleon tournament may be claimed.

No weighted winner score is used. Reveal reports preregistered paired contrasts only.
