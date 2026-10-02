# Modal–phase minimum first release report (P0–P2.5) — 2026-09-13

Copy-on-write only. Parents A034-v0.2.1, A037-v0.3.1, A038-v0.4.0, A029-v0.2.0, A030-v0.2.0, and A035-v0.3.0 were not edited. C006 / A031 / A021 / A030-v0.3.0 / A035-v0.4.0 / A024/A016 were not started.

## New version directories

| Family | New | Parent |
|--------|-----|--------|
| A034 | `A034-v0.2.2` | v0.2.1 |
| A037 | `A037-v0.3.2` | v0.3.1 |
| A038 | `A038-v0.5.0` | v0.4.0 |
| A029 | `A029-v0.3.0` | v0.2.0 |

Workbench additions: `10_docs/registry/schemas/SST_MODAL_PHASE_CONTRACT-1.0.json`, `07_scripts/validate_modal_phase_contract.py`, provenance files under `10_docs/migration/`.

## Parent hashes (unchanged after implementation)

| Artefact | SHA-256 |
|----------|---------|
| A034-v0.2.1 tree | `fa4dd669369fdc4ee07358f062127d0f66513f94771659ef03dd179815b76ef4` |
| A034-v0.2.1 CAMPAIGN cert | `a18f95d1d51cf947b527e7f081aff8e8bb026b97b8663cb99599d21d369a6e47` |
| A037-v0.3.1 tree | `e1f9cabfba7959aa3b7120b20ac0a75b7a8158b9be29e5f503a101b659ef9727` |
| A037-v0.3.1 CAMPAIGN cert | `ab0b4582b6b0ea675110dc2d8824b21ec6598de2fa0f93aba7cd1f1c760829fd` |
| A038-v0.4.0 tree | `f6730ddf33bc1ae1b191bd3ae5a73dbfd2b1a98a92b50c2e8c69e88ddeef489f` |
| A038 overnight `upstream_certs.json` | `b841ea22d9ad0df3d1597e8aacb39b9ece0e7d41ee1c6451da1fd6f104ba97d3` |
| A029-v0.2.0 tree | `2a0f1154e532e13b2419d6ae4c60733d135787664e865e621e95257ab1c46aaf` |

Rollback: set each `FAMILY.yaml` `latest` back to the parent, delete the four new version directories, drop this programme’s `PATCH_LEDGER.jsonl` rows, regenerate catalog indexes. Do not run `catalog_metadata.py --apply`. Per-pack `rollback/PARENT_VERSION.json` records the same hashes.

## Test matrix

| Step | Before (frozen parent) | After (new versions + amendments) |
|------|------------------------|-----------------------------------|
| Workbench paper-upgrade certificate/certs/gates | 33 passed | 33 passed (plus 19 contract tests; 52 combined) |
| A034 package + gate `--selftest` | 14 passed / PASS (v0.2.1) | 20 passed / PASS (v0.2.2) |
| A037 gate `--selftest` | PASS (v0.3.1; no `tests/`) | PASS + 5 symmetry-block tests (v0.3.2) |
| A038 package + gate `--selftest` | 11 passed / PASS (v0.4.0) | 17 passed / PASS (v0.5.0) |
| A029 package + gate `--selftest` | 23 passed / PASS (v0.2.0) | 51 passed / PASS (v0.3.0) |
| Catalog registry / hierarchy | pre-existing A043 / `FAMILY (1).yaml` failures | unchanged: 6 failed, 15 passed (A043 missing `FAMILY.yaml`) |

Frozen workbench pins remain A034-v0.2.0 / A037-v0.3.0 / A038-v0.4.0.

## A034-v0.2.2 curvature-proxy bridge

Historical parent names `{g, H, C_constraint}` and `tangent_hessian_eigenvalues` are provenance-only. New arrays are `C = P H_parent P` and `C_j = P_j C P_j`. Reconstruction error 0. Cluster `{0.0}` and repeated `{0.25364441, 0.25364441}`; `basis_is_unique: false`. `dynamic_stability_claim: false`, `physical_energy_hessian_claim: false`. Parent classification `ENERGETICALLY_ADMISSIBLE` is `historical_parent_only`. Wrapper `A034_BRIDGE_1` passed. Small copies: `A034-v0.2.2/exports/`.

## A037-v0.3.2 symmetry blocks

Matrix `[[1,0,0],[0,1,1],[0,1,1]]`, blocks `[[0],[1,2]]`, labels `body_x/body_y/body_z`. `measured_response_claim: false`. Tied to parent CAMPAIGN `gate_input_sha256` `6980f4b2…e436`.

## A038-v0.5.0 dispatch

Overnight fixture bundle evaluates as `BLOCKED_PROVENANCE` (`geometry:provenance:fixture`, `mesh:provenance:fixture`). A034/A037 certs in that bundle are not the block. A030/A035 are absent and non-required. `QUALIFIED_FOR_MODAL_ANALYSIS` is dispatch eligibility only.

## A029-v0.3.0 accounting / residual

Holonomy: `embedded_in_k`, `phi_holonomy_explicit = 0`. Target metadata now records `temporal_frequency_source`, `return_phase_source`, `spatial_mode_basis_source`, `predicted_omega_used_in_extraction`, `predicted_vg_used_in_extraction`. A frozen modal spatial basis is never labelled fully model-independent. `tau_return` is audited separately; `L/|vg|` is sensitivity-only and, when used as a detector, downgrades the residual.

Execution was reanalysis of 16 frozen `A029-v0.2.0/outputs/basic/blind/cases/` records (~1 s). No new campaign. No \(k_{\rm ref}\) eigensolve: historical JSON has no mode vectors, and a native rebuild is not required to decide the residual (no independent target). A bounded \(k_{\rm ref}\) campaign would need the C++ extension and would not create an independent phase.

Independent time-domain phase target: **no**. Independent phase-blind \(\tau_{\rm return}\): **no**.

| Certificate | Status | SHA-256 |
|-------------|--------|---------|
| `PHASE_ACCOUNTING_CERTIFICATE.json` | `ACCOUNTING_IDENTITY_CONFIRMED` (6/6 evaluable; 0 failed) | `793611f588c93e1c877e3cbc43cf638cc8afa05cf019488582d8f2f2697ac3eb` |
| `PHASE_RESIDUAL_CERTIFICATE.json` | `INDETERMINATE_NO_INDEPENDENT_PHASE_TARGET` | `25e4586d76748760f117b9232e9160cf53f08ca15f5353ffdd39ec9df141acbe` |

Secondary residual reason: `INDETERMINATE_NONINDEPENDENT_RETURN_TIME`. Blindness: `RETROSPECTIVE_PREDICTION_LOCKED`. `scientific_pass: false`.

PRED_M0–PRED_M3 were **not** scored (derived \(\Phi_{\rm loop}\) is not an admissible target).

| Model | CRMSE | Skill \(S_M\) | median \(\|R_\Phi\|\) | CI\(_{95\%}\) | eligible carriers |
|-------|-------|---------------|----------------------|---------------|-------------------|
| PRED_M0–PRED_M3 | n/a | n/a | n/a | n/a | 0 |

Required tables written (JSON sidecars in `A029-v0.3.0/exports/`; Parquet under `outputs/p25_historical/paper_upgrade/`, not committed): `phase_contract`, `dispersion_contract`, `phase_predictor_inputs`, `phase_decomposition_summary`, plus `return_time_contract`.

No ambiguous continuation branches: same-branch \(k_{\rm ref}\) solves were not performed. Stored \(k_{\rm hat}\) matches reconstructed \(k_{\rm closed}\) on all 16 rows. No numerical warnings beyond the already-gated parent `phase_uncertainty_rad` values (accounting only).

## Catalog / family

Canonical `FAMILY.yaml` latest: A034 v0.2.2, A037 v0.3.2, A038 v0.5.0, A029 v0.3.0. `catalog_index.json` and `family_hierarchy.json` already contain those directories. A030 remains v0.2.0 and A035 remains v0.3.0. Catalog tests still fail on pre-existing A043; not introduced here.

## Recommended next branch (not implemented)

**E — no independent target.** Obtaining a provenance-clean independent time-domain modal phase **and** a phase-blind return event is the immediate prerequisite before P3. Branches A–D cannot be decided from ACCOUNT_M3.

### Next version (plan only): A029-v0.4.0 independent-observable capture

Scope: additive recorder on the existing eigenbranch. Do not retune v0.3.0 accounting, do not start C006/A031/A021/A030/A035.

1. During a bounded CLOSED analyze (reuse frozen geometries; no new long campaign), write the raw complex modal coefficient \(a_m(t)\) on a protocol-fixed time grid **before** any \(\omega\) demodulation or \(v_g\)-centered window.
2. Freeze and hash: spatial basis / projector, detector \(C_{\rm envelope}^{\rm raw}\), \(\tau_{\min}\), \(W_{\rm frozen}\) (must not be \(L/|v_g|\) or \(\omega\)-centered), and `THRESHOLDS_FROZEN.json`.
3. Emit `target_independence.class = independent_time_domain_given_frozen_spatial_mode` only when `predicted_omega_used_in_extraction = false` and `predicted_vg_used_in_extraction = false`. Never call a modal-projected target fully model-independent.
4. Emit `tau_return_independence.class = raw_trajectory_phase_blind` only when predicted \(\omega\), predicted \(v_g\), synthetic wavepacket, and \(L/|v_g|\) are all unused. Keep \(L/|v_g|\) as a non-gating diagnostic column.
5. Seal `H_data` … `H_prediction`, then score PRED_M0–PRED_M3 against \(\Phi_{\rm target,ind}(\tau_{\rm return,ind})\). Label `RETROSPECTIVE_PREDICTION_LOCKED` unless target secrecy is hashed.

Expected falsification gates:

- Missing raw series or detector uses \(\omega\)/\(v_g\)/\(L/|v_g|\) → remain `INDETERMINATE_*`; do not score \(\Phi_{\rm loop}\).
- Independent target exists and PRED_M3 skill \(S_3\ge 0.30\) with CI lower \(>0\) and median \(|R_\Phi|\) within the frozen 0.35 rad / \(2\sigma_\Phi\) floor → residual PASS (classical decomposition predicts held-out phase). Then compare nested increments to choose A/B/C.
- Independent target exists and PRED_M3 does not beat PRED_M0 → residual FAIL, then and only then open P3 (strain-history / strain-slew / moving-eigenbasis geometric phase / nonlinear coupling).

Do not implement A029-v0.4.0 or P3 in this release.
