# A056 v0.1.1 — SST Quantum-Number Rosetta Mega Falsifier

Framework: **SST Falsifier Framework v1.0.6**. Source: embedded frozen **E011 SKLSA v0.3.0 STATIC_READY** archive.

## v0.1.1 addition

P06 adds a speculative **gravity/vorticity chiral-selection** test derived from a privately committed historical SST precursor. The precursor is hypothesis lineage only, never evidence. P06 first verifies that parity-even scalar/magnitude controls cannot select handedness, while the registered pseudoscalars `v_g · omega_g` and `omega_g · grad(Phi_g)` reverse sign under parity and swap an analytic axial L/R splitting. Because E011 has no dynamics-ready gravity/vorticity background or independently derived axial coupling scale, the physical mechanism remains `UNRESOLVED` even when the analytic transformation test passes.

The candidate conjugation axis remains separate: global circulation-state reversal in P02. P06 therefore tests C, P and CP as distinct transformations rather than identifying them by definition.

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
8. `run_07_P06_GRAVITY_CHIRAL_SELECTION.cmd`
9. `run_08_P07_U1_CLOSURE.cmd`
10. `run_09_P08_COMPOSITES.cmd`
11. `run_10_finalize_blind.cmd`
12. `run_11_reveal_if_allowed.cmd`
13. `run_12_post_reveal.cmd`

Set `SST_WORKBENCH_ROOT` only if the workbench is not at `C:\workspace\projects\SST-Workbench`. Optional geometry-resolved lanes use E011 source locators and verify raw SHA-256 before use. Unsupported or absent source geometry is reported as UNRESOLVED, never silently synthesized.

## Source boundary

E011 explicitly states that STATIC_READY is suitable for static geometry falsifiers but does not establish finite-core/vortex dynamics, stability, particle identity, or a physical gravity/chiral coupling. A056 preserves that boundary. The embedded atlas covers all prime knots through eight crossings plus selected links; higher-crossing extension is a future source-atlas task.

## Output

All phase outputs accumulate under `A056_SST_Quantum_Number_Rosetta_Mega_Falsifier_v0.1.1-outputs/PHASES/`. Each phase has an independent output manifest. The framework umbrella finalizer then produces the canonical blind gate ledger and package.
