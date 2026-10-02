# Validation — C006 v0.3.0

Validation environment: artifact sandbox, Python fallback backend. This environment is not the canonical SST-Workbench checkout and does not contain the external `07_scripts` paper-upgrade runtime or A029 source tree used by some inherited v0.2.2 tests.

## Syntax

`python -m compileall -q .` — PASS.

## Focused v0.3.0 tests

```text
9 passed
```

Coverage includes complex-spectrum matching, stable-root tracking, descriptive non-oscillatory census, quartet-defect calculation, non-monotonic branch detection, generic QEP self-test, synthetic Darboux factorization self-test, numerical intertwiner, and the rule that a matrix pretest never promotes itself to strict Darboux status.

## Inherited tests in this sandbox

A full inherited `pytest` collection cannot be certified standalone because `test_qualify_split.py` resolves the canonical SST-Workbench root during collection. With workspace-dependent qualification/certificate tests excluded and the single A029 reconstruction test deselected, the portable suite reports:

```text
35 passed, 1 deselected
```

The deselected `mode_recon` case requires the A029 source tree; the inherited certificate/qualification cases require the canonical Workbench `07_scripts` runtime. These are environment prerequisites, not silently converted to scientific passes.

Run the full production validation from the canonical SST-Workbench folder through `run_all.cmd`.

## Phase-V quick fallback validation

Command:

```bash
python run_phase5.py --preset quick --force-python --out-dir <outputs>/phase5
```

Result:

```text
K15 WARN
K16 DIAGNOSTIC
K17 DIAGNOSTIC
K18 PASS
K19 SKIP
K20 SKIP
```

Frozen thresholds were not changed after observing these results.

## Complete quick fallback campaign

The complete five-phase quick campaign was also executed with `--force-python`. It completed with **no hard failures**. K2 was `SKIP` by design because native/Python parity cannot be tested while forcing the Python backend. K6 remained `SKIP` because the RPO was not accepted, so K20 correctly remained locked.

```text
K0 PASS       K1 PASS       K2 SKIP       K3 PASS
K4 PASS       K5 PASS       K6 SKIP       K7 PASS
K8 DIAGNOSTIC K9 DIAGNOSTIC K10 DIAGNOSTIC K11 DIAGNOSTIC
K12 PASS      K13 DIAGNOSTIC K14 PASS      K15 WARN
K16 DIAGNOSTIC K17 DIAGNOSTIC K18 PASS     K19 SKIP
K20 SKIP
```

For K6 the quick fallback run measured `recurrence_rms_over_D = 0.1328875452` and `endpoint_vectorfield_error = 0.2053263280`; no monodromy was constructed.

## Full Phase-V fallback campaign

The stricter Phase-V preset was executed independently with the frozen ladder `N={40,56,72,88}` and `m=1..5`. The status pattern remained:

```text
K15 WARN, K16 DIAGNOSTIC, K17 DIAGNOSTIC, K18 PASS, K19 SKIP, K20 SKIP
```

The QEP self-test remained at machine precision (`max root relative error = 2.22e-16`). None of the five SST common/differential block comparisons passed the frozen Darboux pretest; their off-block coupling ratios were approximately `0.968–0.981`, versus the pre-registered eligibility limit `0.05`.
