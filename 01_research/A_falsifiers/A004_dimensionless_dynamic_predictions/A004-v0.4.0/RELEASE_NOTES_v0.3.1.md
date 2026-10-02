# Release notes v0.3.1

Maintenance hotfix for the bundle-mode analyzer. The numerical campaign engine is unchanged.

## Fixed

The command `python tools/analyze_bundle_modes.py --input outputs ...` recursively discovered older v0.1/v0.2 `campaign_summary.csv` files. Those schemas do not contain `intrinsic_residual`, causing a `KeyError`.

The analyzer now filters schemas and supports explicit campaign inputs.
