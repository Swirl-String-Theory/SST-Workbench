# Validation — Wien–Planck SST Field–Matter Closure Falsifier v0.4.1

Generation-time validation was rerun after the PKLSA-2352/GPU-funnel integration and final fail-closed preflight correction. Production BASIC/EXTENDED/HIGHRES profiles require the native C++17/pybind11 CPU backend. The default GPU route additionally requires Intel oneAPI/SYCL and a GPU↔CPU-native parity gate.

**No SYCL production PASS is claimed in this generation environment.** Intel `icx`/oneAPI is not available here, so the supplied SYCL executable was not compiled or executed. The complete 2352-candidate funnel was instead traversed with the target-identical CPU reference screening metrics at a deliberately small validation resolution.

## 1. Embedded PKLSA integrity

The embedded **PKLSA v0.1.1** validation reports:

```text
families                         49 / 49      PASS
candidates                     2352 / 2352   PASS
variants per family              48          PASS
unique candidate IDs           2352          PASS
finite coordinates                           PASS
PTSA trefoil population          48 / 48     PASS
historical linking cross-check   24 families PASS
selected-variant linking                      PASS
torus grid R > a > 0                          PASS
Gilbert A0/2 L2a1 anchor                       PASS
```

The package copy is kept byte-for-byte consistent with the sealed atlas release and is independently inventoried by `sst_wp.pklsa_inventory`.

## 2. Strict-blind source audit

`validation_reference/BLIND_CODE_AUDIT.json`:

```text
violations = []
pass       = true
```

The audited pre-reveal path now includes the PKLSA adapter/inventory, GPU funnel, GPU parity checker and `gpu/sycl_funnel.cpp` in addition to the v0.3.1 dynamics, seed qualification, mode extraction, energy and action-analysis modules.

No canonical SST constants, SI action scale, \(h\) or \(\hbar\) are permitted in the blind calculation path.

## 3. Python unit/self tests

```text
18 tests run
17 PASS
1 SKIP
```

The single SKIP is the compiled native C++/Python kernel parity test because the native extension is not built in this Linux generation environment.

v0.4.1-specific tests cover:

- exact atlas scope: 2352 candidates / 49 families / 48 variants per family;
- preservation of true multi-component candidates;
- GPU binary protocol roundtrip;
- finite CPU reference screening;
- zero pair-distance strain for rigid-body motion;
- rigid-motion invariance of the Stage-2 shape signature;
- retention of all v0.3.1 iterative-frequency, normal-mode gauge and adaptive-remeshing certification tests.

`python -m compileall -q sst_wp tests` also passes.

## 4. Full-atlas funnel traversal

A complete all-2352 CPU-reference funnel replay was executed with `config/fallback_validation.json`. To keep generation-time cost small, the validation profile uses one survivor per family at each broad stage. It produced:

```text
stage 0 atlas candidates    2352
families                      49
stage 1 survivors             49
stage 2 survivors             49
stage 3 CPU candidates        49
backend                      cpu
```

This is a **pipeline traversal test**, not the production ranking result. Production BASIC/EXTENDED/HIGHRES use the preregistered quotas

\[
2352\rightarrow 392\;(8/{\rm family})\rightarrow98\;(2/{\rm family}).
\]

The full replay confirms that every family can pass through the common adapter, target-free screening metrics, deterministic per-family quota logic, opaque-ID quarantine and Stage-C materialization.

## 5. CPU seed-qualification smoke test

The 49 Stage-C validation candidates were passed through the v0.3.1 CPU qualification logic:

```text
candidate_count = 49
eligible_count  = 49
selected_count  = 1
```

The validation profile intentionally uses permissive thresholds and `require_native=false`; this tests wiring only. Production configurations require native C++ and select at most one finalist per topology family before imposing the global BASIC/EXTENDED/HIGHRES finalist count.

## 6. End-to-end blind/reveal smoke test

The selected validation carrier was run through campaign → blind prepare → blind analyze → reveal. Coverage was complete:

```text
expected observations = 6
OK observations       = 6
```

The funnel preflight embedded in `campaign.json` reports:

```text
funnel_ok             = true
atlas candidates      = 2352
stage-1 survivors     = 49
stage-2 survivors     = 49
screening backend     = cpu
gpu parity required   = false
preflight pass        = true
```

The corresponding `UA0c_PKLSA_funnel_preflight` gate is PASS. The short fallback dynamics still fails the overall blind physics verdict, as intended for a smoke test, rather than manufacturing a Universal-Action claim. Reveal verifies the blind seal and resolves the selected opaque Stage-C file back to its PKLSA provenance record.

For production profiles `require_funnel_preflight=true`; a missing/malformed funnel or a failed required SYCL parity audit aborts the campaign before action dynamics begin.

## 7. Synthetic action controls

Positive dimensionless pipeline control:

```text
blind_pass = true
UA0c funnel preflight = PASS (not required for synthetic control)
```

Classical continuous-action negative control:

```text
blind_pass = false
UA4 reject classical continuous action = FAIL
```

The classical control retains the expected approximately quadratic action-amplitude behavior from the v0.3.1 control family. These synthetic datasets contain no Planck target value and test only scorer logic.

## 8. SYCL status and production parity rule

`validation_reference/GPU_SYCL_EXECUTION_STATUS.json` records:

```text
compiled_in_generation_environment = false
executed_in_generation_environment = false
```

Therefore no Intel Arc/Level-Zero performance or numerical-accuracy claim is made here. On Windows, `run_all.cmd` must:

1. build the CPU-native extension;
2. build the SYCL FP32 broad-screen executable;
3. compare a deterministic sample against the CPU-native reference;
4. satisfy the configured relative-error tolerance;
5. only then execute the 2352-candidate GPU funnel.

The CPU-only alternative `run_all_cpu_fallback.cmd` uses the same screening definitions but is expected to be substantially slower and is explicitly labeled `backend=cpu`.

## 9. Scientific status

v0.4.1 remains a strict-blind **regularized centerline numerical falsifier**. PKLSA is a constructive seed atlas, not independent topology certification; the GPU stages are approximate broad screening, not physics verdicts; and the CPU action solver is not a full three-dimensional finite-core Euler calculation.

A future blind PASS would therefore establish only a dimensionless, numerically certified centerline candidate subject to subsequent finite-core and independent-SI-provenance tests.

## v0.4.1 portability validation

The embedded PKLSA manifest contains no `__pycache__`/`.pyc` records. `verify_atlas.py` is interpreter-independent and was replayed against the complete embedded atlas. Scientific v0.4.0 gates are unchanged.
