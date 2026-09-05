# CHANGELOG v0.3.2

## Partial-failure / resume release

Observed target probe:
- 181 candidates attempted
- 175 PASS
- 6 RUN_FAILED
- failures confined to `drag=on` and all five `dragmag` probes
- `drag=off` passed

### Diagnosis
The drag-enabled logs enter a FreeGLUT/window code path in headless `-nog`
execution. This is a capability limitation of the headless campaign, not evidence
that the trefoil is physically unstable.

### Changes
- Adds `HEADLESS_UNSUPPORTED` status for FreeGLUT/GLUT failures.
- Individual parameter failures no longer abort the full atlas.
- A stage aborts only if zero candidates pass.
- Analyzer recognizes headless incompatibility from both v0.3.2 audits and
  already-existing v0.3.1 log files.
- Adds `run_resume_after_probe.cmd` so the existing 175 successful probe runs
  can be reused without rerunning them.
- Extended stage automatically excludes failed/headless families because only
  accepted probe families are propagated.

Scientific parameter ranges and thresholds are unchanged.
