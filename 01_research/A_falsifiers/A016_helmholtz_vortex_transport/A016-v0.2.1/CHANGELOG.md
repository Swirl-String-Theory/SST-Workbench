# Changelog

## v0.2.1 — 2026-10-07

- Replaces direct `KnotPlot/knots/final` consumption with E010/PKLSA v0.4.0 qualified-carrier ingestion.
- Requires `PKLSA-HIGH-RES-QUALIFICATION-4`, atlas version `0.4.0`, a unique publication-ready release, and per-topology `qualification_gate_pass=true`.
- Adds loaders for PKLSA text XYZ, NPZ, NPY, and JSON carriers.
- HMAC-blinds topology, carrier, source-family, provider-group, and independence identities in public outputs.
- Adds X0 PKLSA cross-source consistency across H2/H3/P3/P4/P5/P6.
- Collapses multiple carrier variants from one provider to one vote; internal disagreement is explicit rather than pseudo-replication.
- Excludes PKLSA-generated/derived carriers from X0 closure while retaining them as diagnostic measurements.
- Keeps all H0-H4 and P0-P6 equations and thresholds from v0.2.0 unchanged.
- Keeps SST Falsifier Framework v1.0.6 frozen and unchanged.

## v0.2.0 — 2026-10-07

- Migrated A016 to SST Falsifier Framework v1.0.6 canonical thin-instance architecture.
- Preserved v0.1.1 H0-H4 thresholds without retuning.
- Added P0-P2 material vorticity-population / volume / flux exact controls.
- Added P3-P6 exterior potentiality, circulation, nonlocal energy, and far-field scaling branches.
- Replaced serial scientific gate logic by a fan-out DAG so an H*/P* FAIL does not suppress sibling measurements.
- Added strict C++17/OpenMP FP64 Biot-Savart certification against Python/NumPy FP64.
