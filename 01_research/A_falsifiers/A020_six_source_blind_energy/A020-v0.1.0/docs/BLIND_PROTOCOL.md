# Blind/preregistration protocol

1. Parse input files and calculate SHA-256 hashes.
2. Freeze configuration and thresholds.
3. Write `00_preregistration_manifest.json` before any physical gate is evaluated.
4. Compute `blind_selection_sha256` from only:
   - the frozen configuration;
   - sorted file-content hashes.
5. Select gate subsets by hashing `blind_selection_sha256 + gate_id + file_hash`.
6. Seed perturbations from `SHA256(file_hash + gate_id)`.
7. Do not load particle masses, particle assignments, alpha targets, or desired topology-dependent values.
8. Preserve every FAIL. No adaptive threshold changes are made after results are visible.
9. BASIC and EXTENDED have separate frozen threshold files.
10. A physical FAIL is not a process failure. Build/calibration/identity errors are the only conditions that make `pipeline_ok=false`.

The resulting outputs can therefore be compared later to an unblinded SST taxonomy without changing the raw campaign.
