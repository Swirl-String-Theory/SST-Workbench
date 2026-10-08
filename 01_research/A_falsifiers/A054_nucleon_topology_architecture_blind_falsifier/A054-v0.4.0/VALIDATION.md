# A054 v0.4.0 validation

**Framework target:** SST Falsifier Framework **v1.0.4 CANONICAL_FROZEN**  
**Status:** **INSTANCE IMPLEMENTATION VALIDATED / PHYSICS UNRUN**

## Local container checks
- exact v0.2 discovery source hashes: **72/72 PASS**;
- opaque source-native confirmation hashes: **7/7 PASS**;
- public forbidden-term scan: **PASS, 0 hits**;
- science-contract completeness proxy check: **PASS**;
- report section-marker completeness: **PASS (16/16)**;
- instance tests: **4 passed, 1 skipped**;
- skipped test: C++/OpenMP native parity because the pybind11 Python package is not installed in this container;
- reduced end-to-end mechanism smoke: **PASS** for BASE, CORE, ELASTIC and CORE+ELASTIC (finite outputs, no numerical exception).

The canonical framework v1.0.4 directory is not mounted in this container/Drive snapshot, so its own 37-test selftest and the instance C++/OpenMP parity must be repeated on the Workbench host. The package is intentionally pinned to the known canonical v1.0.4 framework hashes and fails closed if the expected framework is absent or different.

No scientific A054-v0.4.0 result is claimed by this validation.
