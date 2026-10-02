# Validation — analyzer hotfix v0.3.1

## Reproduced defect

The v0.3.0 command:

```powershell
python tools/analyze_bundle_modes.py --input outputs --output outputs/bundle_mode_analysis
```

failed with:

```text
KeyError: intrinsic_residual
```

because recursive discovery included older campaign-summary schemas.

## Corrective behavior

- Explicit B6 campaign directories are accepted through `--physical-input` and `--numerical-input`.
- Broad recursive `--input` remains supported.
- CSV schemas missing the v0.3 bundle columns are skipped and recorded in `skipped_summary_files.json`.
- Gate calculations operate only on supported axial-bundle rows.

## Tests

```text
12 passed
```

Both broad and explicit analysis routes completed successfully on the mixed release-output tree.
