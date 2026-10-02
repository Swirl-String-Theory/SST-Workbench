# SST Phase-Feedback Delay Knot Stability Blind Falsifier v0.2.1

v0.2.0 is the prospective successor to v0.1.7. It fixes pseudoreplication, prevents train/holdout leakage, measures loop delay with an independent Kelvin packet transport experiment, and uses a dimensionless nonlinear growth response.

\n## v0.2.1 resolver/wrapper hotfix\n\nThis release does **not** change the frozen v0.2.0 scientific protocol or its preregistration lock. It only fixes dataset routing:\n\n- `archive\\...` directories are excluded from automatic production discovery.\n- `run_07_preview_dataset.cmd` propagates resolver exit codes exactly.\n- `run_10_prepare_blind.cmd` uses the same robust exit-code propagation.\n- If two active datasets tie, the resolver deliberately refuses to guess.\n\nPreview an active dataset explicitly, for example:\n\n```bat\nrun_07_preview_dataset.cmd "C:\\workspace\\projects\\SST-Workbench\\KnotPlot\\KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0\\out"\n```\n\nor:\n\n```bat\nrun_07_preview_dataset.cmd "C:\\workspace\\projects\\SST-Workbench\\KnotPlot\\KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.1\\out"\n```\n\nUse the same explicit path with `run_all.cmd` only after the preview passes.\n\n## Confirmatory run

```bat
run_00_install.cmd
run_05_find_input.cmd
run_07_preview_dataset.cmd
run_08_verify_preregistration.cmd
run_all_blind.cmd
run_40_reveal.cmd
```

Or in one command:

```bat
run_all.cmd "C:\path\to\NEW_campaign\out"
```

If no path is supplied the resolver will auto-discover an input directory; for a prospective run, `run_07_preview_dataset.cmd` must still report at least 8 novel unique geometries.

`run_all.cmd` in **confirmatory** mode excludes all identity geometries already seen in the completed v0.1.7 campaign. If fewer than 8 novel unique geometries remain, the result is `INCONCLUSIVE` by preregistration.

## Retrospective audit of the old matrix

To test the code path on the existing v0.1.7 matrix without making a new confirmatory claim:

```bat
run_all_legacy_audit.cmd
```

This deduplicates the old matrix and reports `claim_status = RETROSPECTIVE_ONLY`.

## Outputs

- `blind_work/dataset_audit.json` — counts only, no source labels.
- `blind_work/sealed_manifest.json` — one row per unique blind geometry.
- `results/packet_delay_predictions.json` — packet transport and phase scores.
- `results/nonlinear_measurements.json` — unforced nonlinear growth.
- `results/BLIND_EVALUATION.json` — frozen blind decision.
- `results/REVEALED_EVALUATION.json` — source labels attached after reveal.
- `results/PREPARATION_AUDIT.json` — duplicate/preparation endpoint audit.

See `docs/PREREGISTRATION_v0.2.0.md` for the frozen gates.

## Primary/extended rule

`basic` is the sole primary confirmatory endpoint. `extended` is robustness-only and cannot rescue a basic FAIL.
