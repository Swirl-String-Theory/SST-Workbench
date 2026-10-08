# A056 v0.1.0 — SST Quantum-Number Rosetta Mega Falsifier

Framework: **SST Falsifier Framework v1.0.6**. Source: embedded frozen **E011 SKLSA v0.3.0 STATIC_READY** archive.

## Scientific rule

This is a phased, nonblocking program. Run phases manually in order. A prior FAIL or UNRESOLVED result does **not** prevent the next phase from running; it is inherited only as an evidence-quality annotation. No later diagnostic may convert an earlier gate into PASS.

## Run order (Windows, from this version folder)

Optional: if the canonical framework is not yet installed, run `install_framework_if_missing.cmd`. It never overwrites an already detected v1.0.6 runtime.

1. `run_00_verify.cmd`
2. `run_01_P00_SOURCE_INTAKE.cmd`
3. `run_02_P01_STATIC_STRUCTURE.cmd`
4. `run_03_P02_CONJUGATION.cmd`
5. `run_04_P03_SIGNED_RESPONSE.cmd`
6. `run_05_P04_MONODROMY.cmd`
7. `run_06_P05_INVOLUTIONS.cmd`
8. `run_07_P06_U1_CLOSURE.cmd`
9. `run_08_P07_COMPOSITES.cmd`
10. `run_09_finalize_blind.cmd`
11. `run_10_reveal_if_allowed.cmd`
12. `run_11_post_reveal.cmd`

Set `SST_WORKBENCH_ROOT` only if the workbench is not at `C:\workspace\projects\SST-Workbench`. Optional geometry-resolved lanes use E011 source locators and verify raw SHA-256 before use. Unsupported or absent source geometry is reported as UNRESOLVED, never silently synthesized.

## Source boundary

E011 explicitly states that STATIC_READY is suitable for static geometry falsifiers but does not establish finite-core/vortex dynamics, stability, or particle identity. A056 preserves that boundary. The embedded atlas currently covers all prime knots through eight crossings plus selected links; higher-crossing extension is a future source-atlas task, not fabricated inside this package.

## Output

All phase outputs accumulate under `A056_SST_Quantum_Number_Rosetta_Mega_Falsifier_v0.1.0-outputs/PHASES/`. Each phase has an independent output manifest. The framework umbrella finalizer then produces the canonical blind gate ledger and package.
