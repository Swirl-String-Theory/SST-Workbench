# Modal–phase minimum first release (P0–P2) — 2026-09-13

Copy-on-write adapters only. Parent packs A034-v0.2.1, A037-v0.3.1, A038-v0.4.0, and A029-v0.2.0 were not edited.

## Parent hashes

Recorded in `10_docs/migration/PARENT_HASHES_modal_phase_20260913.json`.

| Artefact | SHA-256 |
|----------|---------|
| A034-v0.2.1 tree | `fa4dd669369fdc4ee07358f062127d0f66513f94771659ef03dd179815b76ef4` |
| A034-v0.2.1 CAMPAIGN cert | `a18f95d1d51cf947b527e7f081aff8e8bb026b97b8663cb99599d21d369a6e47` |
| A037-v0.3.1 tree | `e1f9cabfba7959aa3b7120b20ac0a75b7a8158b9be29e5f503a101b659ef9727` |
| A037-v0.3.1 CAMPAIGN cert | `ab0b4582b6b0ea675110dc2d8824b21ec6598de2fa0f93aba7cd1f1c760829fd` |
| A038-v0.4.0 tree | `f6730ddf33bc1ae1b191bd3ae5a73dbfd2b1a98a92b50c2e8c69e88ddeef489f` |
| A038 overnight `upstream_certs.json` | `b841ea22d9ad0df3d1597e8aacb39b9ece0e7d41ee1c6451da1fd6f104ba97d3` |
| A029-v0.2.0 tree | `2a0f1154e532e13b2419d6ae4c60733d135787664e865e621e95257ab1c46aaf` |
| Overnight log `paper_upgrade_run_log_20260911_225901.md` | `cdfd30df4c8ba1c6c0fbc15955480acdcc4a3829aa57cb2baf194293e337d961` |

Parent A034 and A037 CAMPAIGN hashes were re-checked after implementation and are unchanged.

## Blindness class

`RETROSPECTIVE_PREDICTION_LOCKED`. Historical A029 \(\Phi_{\rm loop}\) and \(\tau_{\rm return}\) were already visible and are constructed from \(\omega\), \(v_g\), and the synthetic wavepacket. They are accounting targets only.

## Nested-model outcome

P2 initially emitted `INDETERMINATE_MISSING_BASELINE_CASES` because discovery missed `{cid}.json` under `blind/cases/`. P2.5 corrected discovery and reanalysed the frozen parent set; see [modal_phase_p25_execution_20260913.md](modal_phase_p25_execution_20260913.md).

P2.5 result: accounting `ACCOUNTING_IDENTITY_CONFIRMED`; residual `INDETERMINATE_NO_INDEPENDENT_PHASE_TARGET` (secondary `INDETERMINATE_NONINDEPENDENT_RETURN_TIME`). PRED_M0–PRED_M3 were not scored. A038 overnight geometry/mesh fixtures dispatch as `BLOCKED_PROVENANCE` and do not authorize `QUALIFIED_FOR_MODAL_ANALYSIS`.

Compact release report: [modal_phase_release_report_20260913.md](modal_phase_release_report_20260913.md).

## Adapter exports

- A034-v0.2.2: `exports/modal_bridge.json` + `exports/A034_BRIDGE_1.json` — reconstruction error 0; `operator_semantics=abs_real_jacobian_curvature_proxy`; no dynamic-stability or energy-Hessian claim.
- A037-v0.3.2: `exports/symmetry_blocks.json` — matrix `[[1,0,0],[0,1,1],[0,1,1]]`, blocks `[[0],[1,2]]`, `measured_response_claim=false`.
- A038-v0.5.0: `provenance_lock` + `modal_dispatch` extend `upstream_gate`; A030/A035 remain non-required.
- A029-v0.3.0: `enable_phase_residual_v1` defaults false on historical presets.

## Test matrix (final)

| Step | Result |
|------|--------|
| Workbench paper-upgrade certificate/certs/gates + new contract tests | 51 passed |
| A034-v0.2.2 `pytest tests` + gate `--selftest` | 19 passed / PASS |
| A037-v0.3.2 symmetry-block tests + gate `--selftest` | 5 passed / PASS |
| A038-v0.5.0 `pytest tests` + gate `--selftest` | 17 passed / PASS |
| A029-v0.3.0 `pytest tests` + gate `--selftest` | 37 passed / PASS |
| Catalog registry tests | pre-existing `FAMILY (1).yaml` failures unchanged |

Frozen workbench pins remain A034-v0.2.0 / A037-v0.3.0 / A038-v0.4.0.

## Rollback

1. Set each canonical `FAMILY.yaml` `latest` back to the parent version and drop the new `versions[]` row.
2. Delete `A034-v0.2.2`, `A037-v0.3.2`, `A038-v0.5.0`, and `A029-v0.3.0`.
3. Restore `10_docs/migration/PATCH_LEDGER.jsonl` to omit this programme’s rows.
4. Regenerate catalog indexes with `build_catalog_index.py` and `build_family_hierarchy.py`.
5. Do not run `catalog_metadata.py --apply`.
