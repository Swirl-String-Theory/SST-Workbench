# F005 v0.5.0-p2 - raw acquisition and initial-state audit

**Scientific status:** `E0_P2_REVIEW_NOT_CERTIFIED`

Existing E0 configuration was NOT changed. No NPY response matrix or DATASET.zip was opened.

## Gates

- `P2_LOCKED_DEVELOPMENT_SPLIT`: `PASS`
- `P2_GEOMETRY_SOURCE`: `SOURCE_DOCUMENTED`
- `P2_STATIC_ACQUISITION_CODE`: `NO_ACQUISITION_FILES_SUBMITTED`
- `P2_INPUT_AXIS`: `BLOCKED_SOURCE_SEMANTICS`
- `P2_HEIGHT_AXIS`: `BLOCKED_SOURCE_SEMANTICS`
- `P2_PREMOTION_RAW`: `BLOCKED_NO_PER_TRAJECTORY_PROOF`
- `P2_HYDRODYNAMIC_REST`: `BLOCKED_NOT_OBSERVABLE_FROM_SCALAR_TRACE`
- `P2_PROVENANCE_ATTESTATION`: `BLOCKED`
- `E0_MAIN_EULER_GATE`: `BLOCKED`
- `E5_EULER_VALIDATION`: `NOT_RUN`
- `E7_PKLSA`: `NOT_RUN`

## Evidence state

- Development split: LOCKED_INPUT_ONLY_SPLIT_VERIFIED
- Acquisition source scan: NO_ACQUISITION_FILES_SUBMITTED
- Robot loader: NO_ROBOT_ZIP
- Acceleration axis: NOT_SUBMITTED
- Height axis: NOT_SUBMITTED
- Pre-motion raw: NO_RAW_PREMOTION_MANIFEST
- P1 relative sign: TRAIN-only hypothesis +1 preferred, NOT independently verified.

## Required source material

Submit the genuine acquisition/export scripts that created INPUT_TRAIN.npy and OUTPUT_TRAIN.npy,
the robot coordinate-frame mapping and the pre-motion raw timestamped traces or per-run logs.
Use `sources/acquisition_evidence/` and then fill `config/P2_EVIDENCE_MANIFEST.json`.
No automatic sign selection or E0 gate promotion is implemented.
