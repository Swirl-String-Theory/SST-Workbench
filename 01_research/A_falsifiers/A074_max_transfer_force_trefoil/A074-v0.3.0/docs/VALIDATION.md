# A074 v0.3.0 Validation — 2026-10-29

**Framework:** self-contained Framework v1.1.0 RC2 selected-runtime snapshot; version not target-machine certified.
**Local tests:** 8/8 PASS; runtime frozen protocol passed; Framework `FULL` produced exact source admissibility manifests, scientific ledger, 6-page LaTeX PDF, and a blind archive. `FULL` returned **exit code 3 by design** because only the genuinely executed Python backend was counted (1 of required 2).

## Genuine P1–P3 outputs

| Grid | Centerline-fit residual | Full-vorticity-field fit | Core radius / cells | Free gap / cells | Unforced energy drift |
|---|---:|---:|---:|---:|---:|
| 32^3 | 0.227956 | 0.447575 | 1.493 | 0.333 | -3.33e-10 |
| 48^3 | 0.233860 | 0.386294 | 2.240 | 0.499 | -1.56e-09 |
| 64^3 | 0.228298 | 0.359235 | 2.987 | 0.666 | -2.47e-09 |

- G0, G1, G2: PASS, restricted to source/initialization/pressure consistency.
- G3: UNRESOLVED: no qualified full-field equilibrium and all grid levels underresolved.
- Framework G7: NOT_APPLICABLE (independent cross-source source not admitted). P3 diagnosed separately by qualification tool; never claim framework G7 PASS.
- Scientific backend matrix: Python FP64 EXECUTED; native C++ NOT_EXECUTED; Intel/GPU NOT_EXECUTED; 2-of-3 qualification BLOCKED.
- No P4 nonlinear-stability, P5 force transfer, or P6 scaling / reveal was executed.
- Time refinement: only 48 cubed grid at fixed 0.1 s. spatial and temporal convergence are different quality gates.
- The finite-core support and nonlocal gap are physically unresolved even on 64 cubed; a large residual is a negative *screening* result only.

## Reproduction and source truth

- `EQUILIBRIUM_SEARCH_v0.2.0.json` is copied without modifications from user-provided result.
- `trefoil_ideal_3_1_1.json` is copied without modifications from previous A074 v0.2.0.
- All three runs use the exact same candidate UUID SHA-256 of the input and candidate geometry.
- Original FULL output's SHA manifest and independent science evidence manifest verified using embedded Framework 1.1.0 runtime.
- 1.1.0 RC2 selected source snapshot contains 47 SHA-256-listed files; not a fully audited native/GPU Framework distribution. FULL certification therefore remains blocked independent of scientific results.
