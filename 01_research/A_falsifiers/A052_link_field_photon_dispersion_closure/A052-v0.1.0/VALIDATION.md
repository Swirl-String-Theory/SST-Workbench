# Validation

Reference validation performed on 2026-10-05.

- Python source import: PASS.
- pytest: 2/2 PASS.
- blind admissibility campaign: PASS.
- PKLSA v0.3.1 provenance snapshot read: PASS.
- geometry-only promotion guard: PASS (promotion refused).
- dynamic eigenmode discovery: BLOCKING (no dynamical generator / k-omega branch in frozen E010 campaign index).
- A044 candidate emission: NOT EMITTED by design.

Scientific verdict: `BLOCKED_NO_DYNAMICAL_EIGENMODE_DATA`.
