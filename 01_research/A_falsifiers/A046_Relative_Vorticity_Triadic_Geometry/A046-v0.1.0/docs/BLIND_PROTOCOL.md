# Blind protocol

The blind stage contains no canonical SST numbers.

Workflow:

1. `prepare_blind.py`
   - writes a dimensionless configuration manifest;
   - records its SHA-256 hash.

2. `run_blind.py`
   - executes synthetic incompressible controls;
   - evaluates preregistered gates;
   - writes `blind_summary.json`, `case_metrics.csv`, and `blind_report.md`.

3. `seal_blind.py`
   - hashes every blind result file;
   - writes `BLIND_SEAL_SHA256.txt`.

4. `reveal.py`
   - verifies the seal;
   - only then imports canonical SST reference values;
   - writes a separate canonical-scale evaluation under `REVEALED/`.

No reveal value is used to choose an ansatz coefficient or tolerance.
