# Phase 2 - exact remaining patch list

No listed successor or production patch was applied. Current Phase 2 only records integrity/admission decisions.

## P01 - SOURCE_RESTORATION_OR_CLEAN_SOURCE_SELECTION

Stage: BEFORE_PILOT_MIGRATION

Use exact sealed RC2/canonical document bytes after retaining the captured local variant, or use a separately admitted clean distribution. Do not regenerate the historical manifest.

Targets:
- `06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10/docs/DD32_FP32X2.md`

Acceptance: Installed framework PACKAGE_MANIFEST all 112 files match, or a clean admitted source pin is explicitly selected; preserved before/after hashes remain available.

## P02 - PILOT_SOURCE_ADMISSION

Stage: BEFORE_A054_MIGRATION

Admit the pinned internally consistent source ZIP, preserving the local Markdown rendering variant; record source selection rather than changing its historical PACKAGE_MANIFEST.

Targets:
- `01_research/A_falsifiers/A054_nucleon_topology_architecture_blind_falsifier/A054-v0.5.1/FALSIFICATION_PLAN.md`
- `01_research/A_falsifiers/A054_nucleon_topology_architecture_blind_falsifier/A054-v0.5.1/README.md`

Acceptance: 59/59 admitted source files match the chosen source manifest; Downloads provenance limit explicitly accepted or independently anchored.

## P03 - PILOT_SOURCE_ADMISSION

Stage: BEFORE_A065_MIGRATION

Admit the pinned source ZIP or preserve exact source variants in a reviewed successor. The Python difference is CRLF/LF only; Markdown differences are math delimiters/EOF. Keep all historical manifests unchanged.

Targets:
- `01_research/A_falsifiers/A065_Triadic_Casimir_Blind/A065-v0.4.3/README_V043.md`
- `01_research/A_falsifiers/A065_Triadic_Casimir_Blind/A065-v0.4.3/docs/QUALIFICATION_V031.md`
- `01_research/A_falsifiers/A065_Triadic_Casimir_Blind/A065-v0.4.3/triadic/report_tex.py`

Acceptance: 159/159 admitted v0.4.3 source entries match; source ZIP provenance limitation documented; all three original dataset seals still verify.

## P04 - RUNTIME_ADMISSION_HARDENING

Stage: FUTURE_A054_SUCCESSOR_AFTER_SOURCE_GATES

Pin qualified v1.0.10 instead of the current v1.0.6 locator; validate manifest self-hash, selected count, E011 index/anchor digests, source-locator joins, raw/geometry hashes, and the exact E010 loader version before source loading. Add tamper and drift rejection tests.

Targets:
- `A054 successor/.sst_framework_root`
- `A054 successor/a054_state/pklsa.py`
- `A054 successor/source_contract.json`
- `A054 successor/tests/test_e013_manifest.py`

Acceptance: Each edited binding/hash is rejected in an isolated regression; unchanged valid manifest loads; stage 30 and no-legacy-evidence rules retained.

## P05 - FAMILY_ADAPTER

Stage: FUTURE_A011_SUCCESSOR_AFTER_SOURCE_GATES

Bind A011_DATASET_ADMISSION.json and the carrier decision ledger; port unchanged geometry definitions into v1.0.10 observed/execution/qualification outputs; preserve separate geometry/proxy and physical/thermodynamic lanes.

Targets:
- `A011 successor/framework pipeline`
- `A011 successor/source and science contracts`
- `A011 successor/tests`

Acceptance: Admitted geometry smoke and Python/native parity pass with existing tolerances; missing physical inputs stay unresolved and cannot promote gravity or energy claims.

## P06 - BLIND_SUCCESSOR_QUALIFICATION

Stage: FUTURE_A065_SUCCESSOR_AFTER_SOURCE_GATES

Reuse the existing v1.0.10 bridge, remove stale version descriptions in the successor, bind the admitted source/adapter pins, and test unique run retention and negative-prerequisite qualification without target access or an expensive volume campaign.

Targets:
- `A065 successor/framework_bridge/install.py`
- `A065 successor/framework_bridge/pipeline.py`
- `A065 successor/preregistration`
- `A065 successor/tests`

Acceptance: Dataset seals and prior negatives remain unchanged; new commitment is separate; diagnostic PASS never closes physical G3/G4/G8; reveal remains separate.

## P07 - MISSING_SCIENTIFIC_INPUTS_NOT_A_TOLERANCE_PATCH

Stage: BEFORE_PHYSICAL_OR_CROSS_PROVIDER_CLAIMS

Supply independently qualified physical observables for A011/A065 and a second genuinely independent admitted L2a1 provider, or retain the affected claims/topology as unresolved. Never synthesize evidence or weaken minimum-provider rules.

Targets:
- `A011 physical input contract`
- `A054 L2a1 provider admission`
- `A065 physical source/heldout contract`

Acceptance: Per-observable provenance, units, independence and convergence evidence exists; otherwise the scientific gate remains unresolved. Not necessary for a correctly labelled geometry-only software smoke.

## P08 - REMAINING_REGISTRY_REVIEW

Stage: BEFORE_BULK_QUEUE_RELEASE

Review unresolved suffix/work/report directories and select canonical latest for imported nonpilot families from release evidence. Fix the generic hierarchy scanner duplicate-version-ID handling before relying on a full rebuild.

Targets:
- `10_docs/registry/catalog_index.json`
- `10_docs/registry/family_hierarchy.json`
- `Affected FAMILY.yaml files listed in registry_reconciliation.json`

Acceptance: Each remaining location has an explicit disposition and each bulk job has an evidence-backed source version. Preserve all archive/report variants.

Pending latest: A003, A046, A047, A049, A052, A053, A055, A056, A057, A058, A059, A060, A061, A062, A063, A064, A066, A067, A068, A069, A070, A071, A072, A073, A074

Unresolved locations:
- A054_nucleon_topology_architecture_blind_falsifier: A054-v0.2.0-r2_native_runner_restore_v2, A054-v0.4 (1).0-r3, A054-v0.4 (2).0-r3
- A055_Blind_Topological_Particle_Spectrum: A055-v0.3.1-execution
- A063_Hicks_Hill_Euler_Separatrix_Falsifier: A063-v0.1.0_external_reports, A063-v0.1.1_external_reports
- A068_PKLSA_PhaseClock: A068-v0.2.0_installer, A068_PKLSA_PhaseClock_v0.3.0_v1.0.8_PRESETUP, A068_PKLSA_PhaseClock_v0.4.0_Framework_v1.0.8_PRESETUP, A068_PKLSA_PhaseClock_v0.4.2_Framework_v1.0.8_A004_PATCH, A068_PKLSA_PhaseClock_v0.4.3_Framework_v1.0.10_GPU_FULL_DIAGNOSTICS, A068_PKLSA_PhaseClock_v0.4.4_Framework_v1.0.10_LONG_TUBE_GPU_DIAGNOSTICS
- A069_3D_SwirlClock_Emergence: A069_v0.6.3_FULL_GPU
- A070_SST_AbsoluteTime_ClockDistance_Cosmology: A070_RotatingCylinder_AxialPulse_v0.2.3_PLAN
- A073_TPDET: TPDET_v0.1.0_DEVELOPMENT

## P09 - PRODUCTION_WORKER_AND_SCHEDULING

Stage: AFTER_THREE_PILOTS_VALIDATED

Implement reviewed per-family execution adapters, transactional claims/recovery, bounded smoke budgets, report-only PDF publication and retention tests. Configure scheduling only after pilot acceptance.

Targets:
- `07_scripts/sst_migration production worker`
- `Central durable queue/event store`
- `Scheduled configuration`

Acceptance: One falsifier per invocation; crash/retry cannot overwrite versions/results; three gate axes preserved; Scheduled stays disabled until actual acceptance.
