# A058 v0.2.6 — preregistered falsification plan

1. Confirm reset R2 switch OFF and S3=1.40 per user-provided GUI defaults; runtime-readback takes precedence as a disagreement warning/fail, but S3 may be omitted by the getter.
2. Build six independently enabled sector reference contexts. R2-ON holds S3=1.40 and measured companion S4 default.
3. Create **one independent R2-OFF activation control**, with identical numeric R2 defaults. Compare it only against the R2 ON reference, not against scalar strength sweeps.
4. Sweep S0–S7 individually on exact `m_k=2^(k/4)`, k=-16..16, with a zero endpoint. 6+1+8×33=271 conditions.
5. Use a single KnotPlot process per condition with `go 32` adaptive observations. Never use a fixed final iteration count.
6. Preserve Damped + collision-fast safety and all other reset-all defaults. Reject bad setters, unsafe runs and frozen contract mismatches.
7. Compute normalized shape, edge-spacing, scalar and iteration-time responses. Report the R2 activation contrast separately. Verify C++ FP64 parity where available; preserve diagnostic continuation across scientific failures.

### One shared admissible initial condition
- Before FREEZE, measure `close` after `reset all`, then prepare the 300-bead catalogue trefoil once with `fitto mindist (1.05*close_0)` as a geometry normalization, not a dynamics-parameter change.
- Save **one** ASCII curve at install, reload it, verify `safe` before/after `go 1`, and record SHA256 and exact KnotPlot executable provenance.
- The production 271 conditions all load this saved single seed; no per-condition fitting, refinement, or raw catalogue reloading is allowed.
- This changes absolute initial shape scale, so all results are explicitly conditional on the seed normalization; no claim of physical uniqueness/scale invariance.
