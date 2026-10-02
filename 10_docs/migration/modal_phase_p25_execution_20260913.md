# Modal–phase P2.5 execution / reveal — 2026-09-13

P0/P2 initially reported `INDETERMINATE_MISSING_BASELINE_CASES` because discovery looked for `*case*.json` and missed A029 `{cid}.json` files under `blind/cases/`. Those records were on disk.

## Frozen execution set

Reanalysis only. No new campaign. No \(k_{\rm ref}\) eigensolve (`k_ref_eigensolve=not_performed_reanalysis_only`). C006 / A031 / A021 were not started.

| Source | Role |
|--------|------|
| `A029-v0.2.0/outputs/basic/blind/cases/*.json` | Execution set (16 parent basic records) |
| On-disk `A029-v0.1.0` / `v0.1.1` / `v0.1.2` case trees | Inventory counts only (720 / 1296 / 1280) |
| `SST_Finite_Core_Axial_Toroidal_Phase_Delay_Blind_Falsifier_v0.1.2_outputs.zip` | Hashed in place, not ingested |

v0.1.2 archive SHA-256: `8d2686aac183947c01e61da0e3898428800af89be0cf539f68dd9937b3f00fe3` (15 689 552 bytes).

Case-file inventory SHA-256: `9d04aa083dd481000a1cf8dc1dd97d18ccf48a2d00a458544ebafee19de48ce3` (see `A029-v0.3.0/exports/FROZEN_CASE_INVENTORY.json`).

## Independence audit

Every ingested record is an `analyze()` product. \(\Phi_{\rm loop}=\operatorname{wrap}(-\omega\tau+\arg A_{\rm env})\) and \(\tau_{\rm return}\) come from `wavepacket_return`. No raw complex trajectory / phase-blind envelope was stored beside the case JSON.

| Gate | Class |
|------|--------|
| Target phase | `derived_from_predictors` |
| Return time | `derived_from_predicted_dispersion` |
| Blindness | `RETROSPECTIVE_PREDICTION_LOCKED` |

Six CLOSED rows have a finite derived loop phase. The other ten are symmetric-\(k\) controls without a stored phase.

## Certificates

Small copies live under `A029-v0.3.0/exports/`. Bulk `outputs/` were not added to git.

| Artefact | Status | SHA-256 |
|----------|--------|---------|
| `PHASE_ACCOUNTING_CERTIFICATE.json` | `ACCOUNTING_IDENTITY_CONFIRMED` (6/6 evaluable, 0 failed) | `793611f588c93e1c877e3cbc43cf638cc8afa05cf019488582d8f2f2697ac3eb` |
| `PHASE_RESIDUAL_CERTIFICATE.json` | `INDETERMINATE_NO_INDEPENDENT_PHASE_TARGET` | `25e4586d76748760f117b9232e9160cf53f08ca15f5353ffdd39ec9df141acbe` |

Residual `scientific_pass` is false. Secondary reason: `INDETERMINATE_NONINDEPENDENT_RETURN_TIME`. PRED_M0–PRED_M3 were not scored. ACCOUNT_M3 vs reconstructed \(\Phi_{\rm carrier,derived}\) confirms \(\omega=\omega_{\rm adv}+\omega_{\rm intrinsic}\) only.

## Tests

| Step | Result |
|------|--------|
| A029-v0.3.0 `pytest tests` | 51 passed |
| A029 paper-upgrade gate `--selftest` | PASS |
| Workbench contract + paper-upgrade certificate/certs/gates | 51 passed |

## What this does not authorize

P3 remains gated on an independent residual that PRED_M3 does not explain. Obtaining a raw time-domain phase **and** a phase-blind \(\tau_{\rm return,ind}\) is the prerequisite. Algebraic ACCOUNT_M3 agreement is not that residual.
