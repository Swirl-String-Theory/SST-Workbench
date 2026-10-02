# A029-v0.3.0 phase accounting / residual

Holonomy is represented once, inside \(k(\Theta_B)\). Historical \(\Phi_{\rm loop}\) and synthetic \(\tau_{\rm return}\) are accounting-only.

`enable_phase_residual_v1` defaults false on historical presets. P2.5 reanalyses frozen parent case JSON rather than starting a new campaign. Target metadata records `temporal_frequency_source`, `return_phase_source`, `spatial_mode_basis_source`, `predicted_omega_used_in_extraction`, and `predicted_vg_used_in_extraction`. A frozen modal spatial basis is never labelled fully model-independent. \(L/|v_g|\) is a non-gating sensitivity diagnostic; using it as a return detector keeps the residual indeterminate.

## P2.5 execution (2026-09-13)

Frozen set: `A029-v0.2.0/outputs/basic/blind/cases/` (16 analyze records). Ten are symmetric-\(k\) controls without a stored loop phase; six CLOSED records have derived \(\Phi_{\rm loop}\) and synthetic \(\tau_{\rm return}\).

| Certificate | Status |
|-------------|--------|
| `PHASE_ACCOUNTING_CERTIFICATE.json` | `ACCOUNTING_IDENTITY_CONFIRMED` (6/6 evaluable; 0 failed) |
| `PHASE_RESIDUAL_CERTIFICATE.json` | `INDETERMINATE_NO_INDEPENDENT_PHASE_TARGET` |

Secondary residual reason: `INDETERMINATE_NONINDEPENDENT_RETURN_TIME`. Blindness class: `RETROSPECTIVE_PREDICTION_LOCKED`. PRED_M0–PRED_M3 were not scored. No raw time-domain trajectory was present beside the case JSON.

The FAMILY baseline zip `SST_Finite_Core_Axial_Toroidal_Phase_Delay_Blind_Falsifier_v0.1.2_outputs.zip` was hashed in place and not ingested. C006 / A031 / A021 were not started.
