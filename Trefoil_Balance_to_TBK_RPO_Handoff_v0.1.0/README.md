# Trefoil_Balance_to_TBK_RPO_Handoff_v0.1.1


## v0.1.1 runtime hotfix

`run_all.cmd` now probes the v0.4.8 DD32 worker before the adaptive spectral
stage. If the external worker is unavailable, the same locked spectral ladder
runs on CPU/OpenMP automatically.

If v0.1.0 already completed the 8-input FP64 screen, overlay the v0.1.1 patch
and run:

```bat
run_resume_after_screen_v048.cmd
```

The resume route recomputes the upstream-only selection, verifies its selection
lock, then proves that the existing screen's unblind manifest has exactly the
same blinded source hashes before reusing it.

Ready-to-run bridge from the Trefoil Balance campaign into the existing
MultiTopology TBK/RPO falsifier.

## Expected repository layout

Place this directory at repository root:

```text
SST-Workbench/
├─ Trefoil_Balance_to_TBK_RPO_Handoff_v0.1.0/
├─ KnotPlot/
│  └─ Trefoil_Balance_Point_Campaign_v0.1.0/
│     ├─ balance_design.json
│     └─ out/
└─ SST_Trefoil_Lobe_Orientation_Blind_Falsifier/
   ├─ SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact/
   └─ SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.6_DD32_compact/
```

The defaults therefore match:

```text
KnotPlot/Trefoil_Balance_Point_Campaign_v0.1.0/out
```

exactly.

## Preferred run — v0.4.8

```bat
run_all.cmd
```

`run_all.cmd` automatically prefers v0.4.8 when it exists.

Equivalent explicit chain:

```bat
run_00_install.cmd
run_02_preflight_v048.cmd
run_05_prepare_handoff.cmd
run_06_verify_selection_lock.cmd
run_10_screen_v048_fp64.cmd
run_20_spectral_v048_dd32.cmd
run_30_confirm_v048_fp64.cmd
run_40_summarize.cmd
run_90_pack_outputs.cmd
```

If SYCL/DD32 is unavailable, keep the same locked candidate set and substitute:

```bat
run_20_spectral_v048_cpu.cmd
```

before the FP64 confirmation.

## v0.4.6 fallback

```bat
run_all_v046.cmd
```

This uses the v0.4.6 custom `run_panel` API with `configs/archive_full.json`
and CPU/OpenMP FP64.

## Candidate modes

Default downstream set:

```text
selected
```

Alternative manifests are prepared at the same time:

```text
prepared/selected
prepared/core
prepared/full_balance
prepared/all20
```

To run a different set manually:

```bat
".venv\Scripts\python.exe" dispatch_target.py --prefer v048 screen-v048 --mode core
```

and use the same `--mode core` for spectral/confirm/summarize.

## Outputs

```text
analysis/BALANCE_SELECTION_ANALYSIS.json
analysis/PREPARED_SUMMARY.json

prepared/<mode>/PUBLIC_ENTRIES.json
prepared/<mode>/PRIVATE_PROVENANCE.json
prepared/<mode>/SELECTION_LOCK.json

tbk_outputs/v048/...
tbk_outputs/v046/...

analysis/TBK_RPO_HANDOFF_SUMMARY.md
analysis/TBK_RPO_HANDOFF_SUMMARY.csv
```

The summary unblinds only after target execution and keeps the target's own
PASS/FAIL and gate semantics intact.

## Overrides

Optional environment variables:

```bat
set TREFOIL_BALANCE_OUT=C:\path\to\out
set TREFOIL_BALANCE_ROOT=C:\path\to\Trefoil_Balance_Point_Campaign_v0.1.0
set SST_TBK_TARGET=C:\path\to\chosen\target
```

No source tree modification of v0.4.8 or v0.4.6 is required.
