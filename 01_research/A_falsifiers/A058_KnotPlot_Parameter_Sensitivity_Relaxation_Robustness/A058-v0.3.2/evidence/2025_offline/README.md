# Offline evidence snapshot

This subfolder contains the deterministic analysis performed on the original user-provided `kpdist-23mar2025.zip` in the current run. These are observations derived from the user's archive, without repackaging the distribution or KnotPlot executable. The SHA-256 of the source archive is stored in each source evidence receipt.

Do not interpret the embedded negative controls as having run against the 2026 native executable. `RUN_RECEIPT.json` explicitly states `native_experiment: NOT_RUN`. On Windows you should run `AUDIT_ALL` against your own retained original archive and compare the resulting SHA-256, catalog metrics and checks before performing optional native probes.
