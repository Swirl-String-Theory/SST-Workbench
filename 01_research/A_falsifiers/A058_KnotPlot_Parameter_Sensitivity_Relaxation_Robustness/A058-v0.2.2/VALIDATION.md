# A058 v0.2.2 validation

Validation date: 2026-10-13.

## Package checks

- Python compile: PASS.
- Instance/package tests: 12/12 PASS.
- Windows `.cmd` launchers start directly with `@echo off`: PASS.
- Release contamination (`__pycache__`, `.pytest_cache`, build trees, venvs, binaries, outputs): none.
- Standalone `FALSIFIER_REPORT.tex` pdflatex compile: PASS.

## Framework-v1.0.6 contract simulation

Exact v1.0.6 validator modules were used for the contract/freeze simulation.

- science contract errors: `[]`
- source contract errors: `[]`
- gate-plan errors: `[]`
- report-contract errors: `[]`
- blind-tree hits: `[]`
- forbidden-term commitment terms: 12
- FREEZE: PASS
- frozen verification: PASS
- final simulated protocol bundle SHA-256: `6aac2e7f5be8074603fb22667d5bb628a593a8188109c31eff0609a3abea6eb1`

## Campaign design checks

- topology count: 1 (anonymous T00; private map binds the catalogue trefoil)
- GUI slider axes: 7 anonymous axes S0-S6
- force-sector references: 5 anonymous references R0-R4
- registered conditions: 236 = 5 references + 7 x 33 non-default perturbations
- ladder: exact `m = 2^(k/4)`, `k=-16..16`, with sector reference supplying `m=1`, plus an exact-zero endpoint
- fixed terminal `ago 1000` / `ago 15000`: absent
- adaptive observation quantum: `go 32`
- stop rule: four consecutive shape+scalar plateau windows after minimum warm-up
- maximum-iteration value: safety cap only; reaching it is explicitly non-convergence
- non-slider geometry overrides (`fitto`, `close`, `max-dr`, `stusplit`, `timeincr`): absent from production runner
- Damped source: `reset all` documented default
- No-Collide/collision avoidance: `collision fast`
- ignored GUI sectors requested by user: not varied
- install integration export: exactly one trefoil ASCII export; only `go 1` is used as a dynamics-liveness check

## Synthetic end-to-end analysis check

A synthetic 236-condition result tree was generated to exercise the analysis layer.

- manifest conditions: 236
- references: 5
- axes: 7
- perturbation responses: 231
- final coordinate completeness: 1.0
- ladder integrity: PASS
- all seven axis summaries produced: PASS
- S5 parameterization-vs-shape diagnostic produced: PASS
- S6 convergence-time-vs-final-shape diagnostic produced: PASS

## Runtime limitation of this build environment

The actual Windows KnotPlot build 5125 executable is not available inside this build sandbox, so the real GUI/CLI setter probe and adaptive dynamics cannot be executed here. `run_install.cmd` is therefore deliberately authoritative on the user's machine: it resolves the five sector parameter names from the actual `parameters` dump, measures all seven numerical defaults, verifies assignment-form setters, confirms a safe trefoil under the reset + collision-fast regime, advances `go 1`, and exports exactly one trefoil before campaign generation is permitted.

Official KnotPlot documentation used to define the regime states that the default dynamics are damped with collision avoidance and documents `collision fast`, `go niter`, `parameters`, and `parameter = value` behavior. Current KnotPlot 1.022 Windows build 5125 is listed by Hypnagogic Software.
