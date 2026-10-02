# Changelog

## v0.3.1
- Adds a blind, diagnostic nonstationary phase/frequency analysis without changing the v0.3.0 primary acceptance logic.
- Selects the analyzed branch from blind dynamics; no hard-coded mode number is introduced.
- Adds linear-versus-quadratic phase model comparison using BIC, segmented-frequency stability, instantaneous-frequency sign consistency, and residual autocorrelation screening.
- Adds per-carrier `nonstationary_phase_carriers.csv` output and primary-baseline diagnostic aggregation.
- Adds synthetic stationary/chirp/random-phase unit tests.
- Adds `SEAL_v0.3.1.json`; v0.3.0 source-panel provenance remains unchanged.

## v0.3.0
- Replaces generated primary geometry with a frozen PKLSA-qualified external source panel.
- Adds raw-source SHA verification and anonymous staging.
- Adds cross-source robust modal-transfer gate using five local transverse holdouts per primary base.
- Removes the post-hoc m=3 target from the primary acceptance criterion.
- Transfers the 1024-step temporal-memory convergence gate to external geometry.
- Preserves v0.2.2/v0.2.3 results as immutable parent evidence.
- Keeps Floquet/RPO inactive.
