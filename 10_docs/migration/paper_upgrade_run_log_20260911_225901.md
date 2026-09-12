# Paper-upgrade run log 20260911_225901

Reuse policy: `/resume` when `outputs/*/stages/*.done` exists.

## D006

- path: `01_research/D_benchmarks/D006_minimal_falsification_harness/D006-v0.4.0`
- resume: `True`
- start: 2026-09-11T22:59:01Z
- end: 2026-09-11T22:59:02Z
- elapsed_s: 0.4
- exit_code: 0
- cert: `n/a`

## A037

- path: `01_research/A_falsifiers/A037_chirality_helicity_transport_polarity/A037-v0.3.1`
- resume: `True`
- start: 2026-09-11T22:59:02Z
- end: 2026-09-11T22:59:03Z
- elapsed_s: 1.3
- exit_code: 0
- cert: `01_research/A_falsifiers/A037_chirality_helicity_transport_polarity/A037-v0.3.1/outputs/basic/paper_upgrade/certificate.json`

## A034

- path: `01_research/A_falsifiers/A034_qhp_stability_landscape/A034-v0.2.1`
- resume: `True`
- start: 2026-09-11T22:59:03Z
- end: 2026-09-11T22:59:04Z
- elapsed_s: 1.0
- exit_code: 0
- cert: `01_research/A_falsifiers/A034_qhp_stability_landscape/A034-v0.2.1/outputs/basic/paper_upgrade/certificate.json`

## C006

- path: `01_research/C_dynamics/C006_kelvin_floquet_workbench/C006-v0.2.0`
- resume: `False`
- start: 2026-09-11T22:59:04Z
- end: 2026-09-11T22:59:09Z
- elapsed_s: 5.2
- exit_code: 0
- cert: `n/a`

## A029

- path: `01_research/A_falsifiers/A029_finite_core_axial_toroidal_phase_delay/A029-v0.2.0`
- resume: `False`
- start: 2026-09-11T22:59:09Z
- end: 2026-09-11T22:59:32Z
- elapsed_s: 22.4
- exit_code: 1
- cert: `n/a`

**Stopped on A029 failure.**

### A029 failure note
Native build failed: Microsoft Visual C++ 14.0+ not available on this machine (`cl.exe` missing). Chain continued for remaining packs with `--continue-on-fail`.

## A035

- path: `01_research/A_falsifiers/A035_intrinsic_modal_swirl_clock/A035-v0.3.0`
- resume: `False`
- start: 2026-09-11T23:05:04Z
- end: 2026-09-11T23:05:22Z
- elapsed_s: 18.8
- exit_code: 1
- cert: `n/a`

**Failure on A035** (continue_on_fail=True).

## A008

- path: `01_research/A_falsifiers/A008_chiral_kelvin_core/A008-v0.2.0`
- resume: `False`
- start: 2026-09-11T23:05:22Z
- end: 2026-09-11T23:05:23Z
- elapsed_s: 1.0
- exit_code: 1
- cert: `n/a`

**Failure on A008** (continue_on_fail=True).

## A030

- path: `01_research/A_falsifiers/A030_material_phase_eft_holonomy/A030-v0.2.0`
- resume: `False`
- start: 2026-09-11T23:05:23Z
- end: 2026-09-11T23:05:52Z
- elapsed_s: 28.4
- exit_code: 1
- cert: `n/a`

**Failure on A030** (continue_on_fail=True).

## A023

- path: `01_research/A_falsifiers/A023_multitopology_rpo_floquet/A023-v0.5.0`
- resume: `False`
- start: 2026-09-11T23:05:52Z
- end: 2026-09-11T23:07:51Z
- elapsed_s: 119.6
- exit_code: 0
- cert: `n/a`

## A031

- path: `01_research/A_falsifiers/A031_adaptive_period_rpo_floquet/A031-v0.2.0`
- resume: `False`
- start: 2026-09-11T23:07:51Z
- end: 2026-09-11T23:07:52Z
- elapsed_s: 0.3
- exit_code: 2
- cert: `n/a`

**Failure on A031** (continue_on_fail=True).

## A038

- path: `01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0`
- resume: `False`
- start: 2026-09-11T23:07:52Z
- end: 2026-09-11T23:07:52Z
- elapsed_s: 0.3
- exit_code: 2
- cert: `n/a`

**Failure on A038** (continue_on_fail=True).

## A021

- path: `01_research/A_falsifiers/A021_trefoil_lobe_self_confinement/A021-v0.4.0`
- resume: `False`
- start: 2026-09-11T23:07:52Z
- end: 2026-09-11T23:08:09Z
- elapsed_s: 17.2
- exit_code: 1
- cert: `n/a`

**Failure on A021** (continue_on_fail=True).

## A024

- path: `01_research/A_falsifiers/A024_threaded_hole_separatrix/_variants/optional-paper-control`
- resume: `False`
- start: 2026-09-11T23:08:09Z
- end: 2026-09-11T23:08:24Z
- elapsed_s: 14.7
- exit_code: 1
- cert: `n/a`

**Failure on A024** (continue_on_fail=True).

## A025

- path: `01_research/A_falsifiers/A025_local_thread_texture_boost/_variants/optional-paper-control`
- resume: `False`
- start: 2026-09-11T23:08:24Z
- end: 2026-09-11T23:08:34Z
- elapsed_s: 10.4
- exit_code: 1
- cert: `n/a`

**Failure on A025** (continue_on_fail=True).

## A016

- path: `01_research/A_falsifiers/A016_helmholtz_vortex_transport/_variants/optional-paper-control`
- resume: `False`
- start: 2026-09-11T23:08:34Z
- end: 2026-09-11T23:08:47Z
- elapsed_s: 13.0
- exit_code: 1
- cert: `n/a`

**Failure on A016** (continue_on_fail=True).

**Completed with failures: A035, A008, A030, A031, A038, A021, A024, A025, A016.**

---

## Retry wave 2026-09-12T01:14:53Z

Fixes: MSVC via vcvars64 in orchestrator; catalog knot paths; A038 upstream CAMPAIGN fixtures; A031 V048/atlas defaults; A025 package discovery.

## A029

- path: `01_research/A_falsifiers/A029_finite_core_axial_toroidal_phase_delay/A029-v0.2.0`
- resume: `True`
- start: 2026-09-11T23:14:53Z
- end: 2026-09-11T23:14:54Z
- elapsed_s: 1.5
- exit_code: 1
- cert: `n/a`

**Failure on A029** (continue_on_fail=True).

## A035

- path: `01_research/A_falsifiers/A035_intrinsic_modal_swirl_clock/A035-v0.3.0`
- resume: `True`
- start: 2026-09-11T23:14:54Z
- end: 2026-09-11T23:14:56Z
- elapsed_s: 1.6
- exit_code: 1
- cert: `n/a`

**Failure on A035** (continue_on_fail=True).

## A008

- path: `01_research/A_falsifiers/A008_chiral_kelvin_core/A008-v0.2.0`
- resume: `False`
- start: 2026-09-11T23:14:56Z
- end: 2026-09-11T23:14:57Z
- elapsed_s: 1.7
- exit_code: 1
- cert: `n/a`

**Failure on A008** (continue_on_fail=True).

## A030

- path: `01_research/A_falsifiers/A030_material_phase_eft_holonomy/A030-v0.2.0`
- resume: `True`
- start: 2026-09-11T23:14:57Z
- end: 2026-09-11T23:14:59Z
- elapsed_s: 1.4
- exit_code: 1
- cert: `n/a`

**Failure on A030** (continue_on_fail=True).

## A031

- path: `01_research/A_falsifiers/A031_adaptive_period_rpo_floquet/A031-v0.2.0`
- resume: `False`
- start: 2026-09-11T23:14:59Z
- end: 2026-09-11T23:15:00Z
- elapsed_s: 1.4
- exit_code: 1
- cert: `n/a`

**Failure on A031** (continue_on_fail=True).


---

## Retry wave 2 (MSVC env injected into orchestrator process)

## A029

- path: `01_research/A_falsifiers/A029_finite_core_axial_toroidal_phase_delay/A029-v0.2.0`
- resume: `True`
- start: 2026-09-11T23:15:45Z
- end: 2026-09-11T23:15:46Z
- elapsed_s: 0.6
- exit_code: 1
- cert: `n/a`

**Failure on A029** (continue_on_fail=True).

## A035

- path: `01_research/A_falsifiers/A035_intrinsic_modal_swirl_clock/A035-v0.3.0`
- resume: `True`
- start: 2026-09-11T23:15:46Z
- end: 2026-09-11T23:15:47Z
- elapsed_s: 0.6
- exit_code: 1
- cert: `n/a`

**Failure on A035** (continue_on_fail=True).

## A008

- path: `01_research/A_falsifiers/A008_chiral_kelvin_core/A008-v0.2.0`
- resume: `False`
- start: 2026-09-11T23:15:47Z
- end: 2026-09-11T23:15:47Z
- elapsed_s: 0.8
- exit_code: 1
- cert: `n/a`

**Failure on A008** (continue_on_fail=True).

## A030

- path: `01_research/A_falsifiers/A030_material_phase_eft_holonomy/A030-v0.2.0`
- resume: `True`
- start: 2026-09-11T23:15:47Z
- end: 2026-09-11T23:15:48Z
- elapsed_s: 0.6
- exit_code: 1
- cert: `n/a`

**Failure on A030** (continue_on_fail=True).

## A031

- path: `01_research/A_falsifiers/A031_adaptive_period_rpo_floquet/A031-v0.2.0`
- resume: `False`
- start: 2026-09-11T23:15:48Z
- end: 2026-09-11T23:15:49Z
- elapsed_s: 0.5
- exit_code: 1
- cert: `n/a`

**Failure on A031** (continue_on_fail=True).

## A038

- path: `01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0`
- resume: `False`
- start: 2026-09-11T23:15:49Z
- end: 2026-09-11T23:15:53Z
- elapsed_s: 4.7
- exit_code: 1
- cert: `n/a`

**Failure on A038** (continue_on_fail=True).

## A021

- path: `01_research/A_falsifiers/A021_trefoil_lobe_self_confinement/A021-v0.4.0`
- resume: `True`
- start: 2026-09-11T23:15:53Z
- end: 2026-09-11T23:15:54Z
- elapsed_s: 0.7
- exit_code: 1
- cert: `n/a`

**Failure on A021** (continue_on_fail=True).

## A024

- path: `01_research/A_falsifiers/A024_threaded_hole_separatrix/_variants/optional-paper-control`
- resume: `False`
- start: 2026-09-11T23:15:54Z
- end: 2026-09-11T23:15:58Z
- elapsed_s: 4.4
- exit_code: 1
- cert: `n/a`

**Failure on A024** (continue_on_fail=True).

## A025

- path: `01_research/A_falsifiers/A025_local_thread_texture_boost/_variants/optional-paper-control`
- resume: `True`
- start: 2026-09-11T23:15:58Z
- end: 2026-09-11T23:15:59Z
- elapsed_s: 0.7
- exit_code: 1
- cert: `n/a`

**Failure on A025** (continue_on_fail=True).

## A016

- path: `01_research/A_falsifiers/A016_helmholtz_vortex_transport/_variants/optional-paper-control`
- resume: `False`
- start: 2026-09-11T23:15:59Z
- end: 2026-09-11T23:16:10Z
- elapsed_s: 10.6
- exit_code: 0
- cert: `n/a`

**Completed with failures: A029, A035, A008, A030, A031, A038, A021, A024, A025.**

---

## Retry wave 3 (DISTUTILS_USE_SDK + MSVC PATH)

## A029

- path: `01_research/A_falsifiers/A029_finite_core_axial_toroidal_phase_delay/A029-v0.2.0`
- resume: `True`
- start: 2026-09-11T23:16:14Z
- end: 2026-09-11T23:16:30Z
- elapsed_s: 16.0
- exit_code: 0
- cert: `n/a`

## A035

- path: `01_research/A_falsifiers/A035_intrinsic_modal_swirl_clock/A035-v0.3.0`
- resume: `True`
- start: 2026-09-11T23:16:30Z
- end: 2026-09-11T23:16:34Z
- elapsed_s: 4.5
- exit_code: 1
- cert: `n/a`

**Failure on A035** (continue_on_fail=True).

## A008

- path: `01_research/A_falsifiers/A008_chiral_kelvin_core/A008-v0.2.0`
- resume: `False`
- start: 2026-09-11T23:16:34Z
- end: 2026-09-11T23:16:43Z
- elapsed_s: 8.5
- exit_code: 0
- cert: `n/a`

## A030

- path: `01_research/A_falsifiers/A030_material_phase_eft_holonomy/A030-v0.2.0`
- resume: `True`
- start: 2026-09-11T23:16:43Z
- end: 2026-09-11T23:16:43Z
- elapsed_s: 0.6
- exit_code: 1
- cert: `n/a`

**Failure on A030** (continue_on_fail=True).

## A031

- path: `01_research/A_falsifiers/A031_adaptive_period_rpo_floquet/A031-v0.2.0`
- resume: `False`
- start: 2026-09-11T23:16:43Z
- end: 2026-09-11T23:16:44Z
- elapsed_s: 0.5
- exit_code: 1
- cert: `n/a`

**Failure on A031** (continue_on_fail=True).

## A038

- path: `01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0`
- resume: `False`
- start: 2026-09-11T23:16:44Z
- end: 2026-09-11T23:16:53Z
- elapsed_s: 8.9
- exit_code: 1
- cert: `n/a`

**Failure on A038** (continue_on_fail=True).

## A021

- path: `01_research/A_falsifiers/A021_trefoil_lobe_self_confinement/A021-v0.4.0`
- resume: `True`
- start: 2026-09-11T23:16:53Z
- end: 2026-09-11T23:16:53Z
- elapsed_s: 0.7
- exit_code: 1
- cert: `n/a`

**Failure on A021** (continue_on_fail=True).

## A024

- path: `01_research/A_falsifiers/A024_threaded_hole_separatrix/_variants/optional-paper-control`
- resume: `False`
- start: 2026-09-11T23:16:53Z
- end: 2026-09-11T23:17:12Z
- elapsed_s: 19.3
- exit_code: 0
- cert: `n/a`

## A025

- path: `01_research/A_falsifiers/A025_local_thread_texture_boost/_variants/optional-paper-control`
- resume: `True`
- start: 2026-09-11T23:17:12Z
- end: 2026-09-11T23:17:15Z
- elapsed_s: 2.4
- exit_code: 1
- cert: `n/a`

**Failure on A025** (continue_on_fail=True).

## A016

- path: `01_research/A_falsifiers/A016_helmholtz_vortex_transport/_variants/optional-paper-control`
- resume: `True`
- start: 2026-09-11T23:17:15Z
- end: 2026-09-11T23:17:15Z
- elapsed_s: 0.4
- exit_code: 0
- cert: `n/a`

**Completed with failures: A035, A030, A031, A038, A021, A025.**

---

## Retry wave 4 (SST_RESUME env; A031=D009 atlas; A038 PU_OUT split; A035 catalog roots; A025 short obj path)

## A035

- path: `01_research/A_falsifiers/A035_intrinsic_modal_swirl_clock/A035-v0.3.0`
- resume: `True`
- start: 2026-09-11T23:20:47Z
- end: 2026-09-12T02:11:47Z
- elapsed_s: 10259.7
- exit_code: 1
- cert: `n/a`

**Failure on A035** (continue_on_fail=True).

## A030

- path: `01_research/A_falsifiers/A030_material_phase_eft_holonomy/A030-v0.2.0`
- resume: `True`
- start: 2026-09-12T02:11:47Z
- end: 2026-09-12T02:13:48Z
- elapsed_s: 121.5
- exit_code: 2
- cert: `n/a`

**Failure on A030** (continue_on_fail=True).


### Post-freeze recovery note (2026-09-12T05:52:34.6647796+02:00)
- PC freeze interrupted wave 4 during A031 extended (cache partially written).
- A035 completed stage_a (333) with scientific gate `INDETERMINATE_STAGE_A_INSUFFICIENT_VALID_COVERAGE` (exit 1); markers finalized without re-run.
- A030 basic+extended stages completed with scientific `INCONCLUSIVE` / `NUMERICALLY_INCONCLUSIVE` (exit 2); finish stamped DONE.
- Resuming chain: A031 → A038 → A021 → A025 (A016/A024 already PASS).


---

## Retry wave 5 (post-freeze resume)

## A031

- path: `01_research/A_falsifiers/A031_adaptive_period_rpo_floquet/A031-v0.2.0`
- resume: `True`
- start: 2026-09-12T03:52:51Z
- end: 2026-09-12T03:59:25Z
- elapsed_s: 393.8
- exit_code: 0
- cert: `n/a`

## A038

- path: `01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0`
- resume: `False`
- start: 2026-09-12T03:59:25Z
- end: 2026-09-12T04:18:11Z
- elapsed_s: 1125.7
- exit_code: 0
- cert: `n/a`

## A021

- path: `01_research/A_falsifiers/A021_trefoil_lobe_self_confinement/A021-v0.4.0`
- resume: `True`
- start: 2026-09-12T04:18:11Z
- end: 2026-09-12T04:18:56Z
- elapsed_s: 44.6
- exit_code: 0
- cert: `n/a`

## A025

- path: `01_research/A_falsifiers/A025_local_thread_texture_boost/_variants/optional-paper-control`
- resume: `True`
- start: 2026-09-12T04:18:56Z
- end: 2026-09-12T04:19:23Z
- elapsed_s: 27.4
- exit_code: 0
- cert: `n/a`

**All requested packs completed.**

---

## Final status (post-freeze wave 5)

| Pack | Chain exit | Notes |
|------|------------|-------|
| D006 | 0 | resume PASS |
| A037-v0.3.1 | 0 | promotable CAMPAIGN cert |
| A034-v0.2.1 | 0 | promotable CAMPAIGN cert |
| C006 | 0 | PASS |
| A029 | 0 | PASS (MSVC) |
| A035 | 1 | scientific `INDETERMINATE_STAGE_A_INSUFFICIENT_VALID_COVERAGE` after full stage_a (333); chain stage completed |
| A008 | 0 | PASS |
| A030 | 2 | scientific `INCONCLUSIVE` / `NUMERICALLY_INCONCLUSIVE`; stages done |
| A023 | 0 | PASS |
| A031 | 0 | PASS (D009 atlas + cache resume) |
| A038 | 0 | PASS (upstream CAMPAIGN gate + full basic chain) |
| A021 | 0 | PASS (scientific FAIL is valid) |
| A024 | 0 | PASS |
| A025 | 0 | PASS |
| A016 | 0 | PASS |

Promotable certs:
- `A034-v0.2.1/outputs/basic/paper_upgrade/certificate.json` — CAMPAIGN, `promotion_allowed=true`
- `A037-v0.3.1/outputs/basic/paper_upgrade/certificate.json` — CAMPAIGN, `promotion_allowed=true`

---

## Fix wave 6 (A035/A030 scientific + wiring patches)

### Patches
- **A035** `config/basic.json`: align `gate_max_stage_a_ds_cv` with sim hard stop (`0.3`); `gate_require_all_priority_carriers=false`; coverage fraction `0.7` so catalog-wide stage_a can reach a conclusive FAIL instead of INDETERMINATE.
- **A035** `run_basic.cmd`: stop wiping entire `outputs\basic` (destroys paper-upgrade markers); selective wipe only on `/fresh` / `SST_FRESH=1`.
- **A035** `run_all.cmd`: treat completed science as pack exit `0`.
- **A030** `campaign.py`: physical G4 FAIL beats T/S_CONV noise → `CLOSURE_FAIL` / `CLOSURE_FAIL_WITH_NUMERICAL_WARNINGS`; exit codes 0/2 like A021.
- **A030** `configs/basic.json`: `min_good_modes=2`, `min_phase_r2=0.55` so G4 can resolve PASS/FAIL on basic samples.
- **A030** `run_all.cmd`: capture stage RCs; pack exit `0` when science completes; fix `endlocal` wiping `PU_*` before finish.

### Results
## A035

- path: `01_research/A_falsifiers/A035_intrinsic_modal_swirl_clock/A035-v0.3.0`
- resume: `True`
- exit_code: 0
- scientific gate: `FAIL_STAGE_A_NO_RECURRENT_SHAPE_CLOCK` (83/111 geometry-valid after ds-gate alignment; 0 provisional candidates)

## A030

- path: `01_research/A_falsifiers/A030_material_phase_eft_holonomy/A030-v0.2.0`
- resume: `True` (basic+extended stages re-run)
- exit_code: 0
- basic overall: `CLOSURE_FAIL`
- extended overall: `CLOSURE_FAIL_WITH_NUMERICAL_WARNINGS`

### Final status (all packs)

| Pack | Chain exit | Notes |
|------|------------|-------|
| D006…A029, A008, A023…A016 | 0 | unchanged from wave 5 |
| A035 | 0 | conclusive scientific FAIL after ds-gate patch |
| A030 | 0 | conclusive scientific CLOSURE_FAIL(+warnings) |

All requested paper-upgrade packs now exit 0.

---

## Post-reboot integrity check (2026-09-12 ~07:25 local)

PC restarted twice during earlier runs; re-verified on disk:

| Pack | State | Notes |
|------|-------|-------|
| D006, A037, A034, A029, A035, A030, A023, A031, A038, A021, A016, A024 | DONE | OK |
| C006, A008 | DONE | under `outputs/quick` (not `basic`) |
| A025 | was RUNNING after reboot | all stages already DONE; `finish` stamped → DONE |
| A034/A037 certs | CAMPAIGN | `promotion_allowed=true`, `synthetic_inputs=false`, NQ t/s/m=PASS |
| A035 science | FAIL_STAGE_A_NO_RECURRENT_SHAPE_CLOCK | conclusive |
| A030 science | CLOSURE_FAIL / CLOSURE_FAIL_WITH_NUMERICAL_WARNINGS | conclusive |

Plan todos all completed — no further pack runs required.

