# SST dark-knot Rayleigh harness v1.1 upgrade notes

This upgrade keeps the numerical kernel unchanged and improves audit semantics.

## Changes

- Fixed the `classify()` normalization bug: `Delta_Omega` is now normalized with the actual `omega` argument, not a missing `rd["Omega"]` fallback.
- Added `schema_version: "0.2.0"` to audit JSON output.
- Added a top-level `source` block describing:
  - base source: generated diagnostic embedding or input CSV;
  - response source: not supplied, proxy, unverified external CSV, Ridgerunner, projected Ridgerunner, or solver;
  - whether proxy response was detected;
  - whether rocking/breathing observables are claim-ready.
- Added `--response-source` to `run_example.py` and `run_sweep.py`.
- Split the canon-safe classification text for `3_1` and `4_1`.
- Added response-evidence labels so proxy or unverified CSVs cannot silently become physical claims.
- Added sweep CSV/JSON fields: `response_source_type`, `proxy_detected`, `provisional_label`, and `claim_ready_for_rocking_breathing`.
- Removed stale compiled artifacts from the release zip; rebuild the optional C++ backend locally.

## Recommended labels

Use this for proxy/smoke tests:

```powershell
python run_example.py --knot 4_1 --input-csv V0_4_1.csv --proxy-response-gain 0.02 --out smoke_proxy_4_1.json
```

Use this for external CSVs that are not yet proven to be solver-derived:

```powershell
python run_example.py --knot 4_1 --input-csv V0_4_1.csv --vertices-plus Vplus_4_1.csv --vertices-minus Vminus_4_1.csv --out audit_4_1_external.json
```

Use this only after the response pair came from a real constrained/projected relaxation:

```powershell
python run_example.py --knot 4_1 --input-csv V0_4_1.csv --vertices-plus Vplus_4_1.csv --vertices-minus Vminus_4_1.csv --response-source projected_ridgerunner --out audit_4_1_projected.json
```
