# A006 v0.5.0c — force/collision qualification science contract

**Scope:** KnotPlot algorithmic force effects, not physical inviscid Euler/PKLSA dynamics.

- G0: identical initial three-component XYZ bytes after numerical parsing for every arm, and immutable input SHA-256.
- G1: controlled one-factor comparisons: BEND_OFF vs BEND_1/10/100; vs MECH_ONLY/ELEC_ONLY; vs AMECH_140_ELEC/AMECH_MATCH_ELEC (effect of initial rest length); vs AMECH_MATCH_ONLY (isolating elec); vs AMECH_MATCH_P2 (power); vs MAXDR_0005/MAXDR_0010; vs CLOSE_010/CLOSE_030. Never compare multiple simultaneous parameter changes as a single-cause attribution.
- G2: no force order confound: `mechforce=off` whenever `amechforce=on`. `afmpower=1` for linear spring; `spring-length` uses source-derived global median edge for MATCH.
- G3: collision mode requested and queried every checkpoint; runtime console output must be saved. `close` varies only in its own branch and always `max-dr < close`. Damped selected via GUI should be verified; we do not invent a console parameter for it.
- G4: accurate checkpoints 0,1,8,32,128, native CSV `/I,/N,/l,/g`, `data close`, no `stop`, and native KnotPlot XYZ read per component using Component headers. Do not infer runtime from prepared scripts.
- G5: derived metrics: maximum & 99th percentile turn, maximum curvature, shortest/median/longest edge, max/min ratio, periodic seam ratio, centroid and length; compare all three components independently. Retain crash/incomplete status and never silently fill gaps.
- G6: do not equate a less sharp shape with topological or hydrodynamical stability. Knot identity and Milnor triple invariant remain independent gates. `symm` not activated without explicit separate qualification.

## Interpretation warnings

The reference `spring-length=1.4` is about 29% shorter than typical initial bead spacing (1.968625). A linear spring whose force depends on elongation relative to rest length could therefore alter the initial force state appreciably. Actual implementation of `amech` must be confirmed by instrumented KnotPlot or source inspection before treating this as a quantitative force-law derivation.

The experiment uses a high-resolution link of 3217 beads. `go beadlimit 4000` is required before the first `ago` and `collision fast` plus the `close` threshold do not certify link topology.

## References

- R. G. Scharein, *KnotPlot Online Parameters*, https://knotplot.com/manual/parameters.html
- R. G. Scharein, *KnotPlot Commands*, https://knotplot.com/manual/commands.html
- R. G. Scharein, *KnotPlot Manual*, https://knotplot.com/doc/KnotPlot-Manual.pdf
