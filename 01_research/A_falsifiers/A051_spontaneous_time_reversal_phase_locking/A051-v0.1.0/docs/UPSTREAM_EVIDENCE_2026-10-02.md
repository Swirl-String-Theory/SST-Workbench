# Upstream evidence used to design A051 — reviewed 2026-10-02

The following results constrain gate design; they are not imported as positive A051 evidence.

- **A045 v0.2.2** `summary.json`: numerical gates G0–G7 PASS, `numerics_verdict=PASS`, `physics_verdict=UNTESTED`, `formal_floquet=SKIP_NO_CERTIFIED_RPO`.
- **A048 v0.2.1** `GATE_STATUS_MATRIX.json` + `euler_probe_summary.json`: overall physical verdict `INDETERMINATE`; 48 authenticated geometries ingested, one independently evolved; energy drift `8.09785571931343e-12`, divergence RMS `1.214472734140234e-16`; core sampling `1.6043 cells/sigma < 4`; `3 sigma kappa_max = 2.1055 > 0.5`; no material-phase observable and no evolved-centerline observable. Therefore A051 refuses to infer phase from geometry.
- **A050 v0.3.0** `blind_results.json`: spatial gate PASS and temporal-memory transfer present/converged on all five bases, but modal-transfer gate FAIL with zero robust bases in both source groups; verdict `REAL_GEOMETRY_MODAL_TRANSFER_NOT_REPRODUCED`; Floquet inactive because no qualified RPO. Therefore A051 requires cross-source/geometry robustness.
- **A031 v0.2.0** extended `REPORT.md`: both tested families classify `NO_CERTIFIED_RPO`; Floquet N/A. Therefore no formal Floquet claim is permitted without a new certified RPO.
- **A038** blind-chain summary: early/core/refine/resolution/temporal/mesh gates qualify numerically; long-window RPO is indeterminate and the RPO/mechanism stages are not run. Therefore seed qualification is useful upstream but insufficient for branch stability.
- **A021 v0.4.0**: overall FAIL; critical reduced-stability and cross-lobe-stabilization gates fail. Therefore A051 does not use self-confinement as a proxy for phase locking.
- **A030** summary: `CLOSURE_FAIL_WITH_NUMERICAL_WARNINGS`. Therefore geometric candidate phase and material phase remain separated.
- **A029** documentation: a positive finite-core return delay is propagation timing, not feedback stabilization or phase-lock closure.

Current canonical metadata discrepancy: `family_hierarchy.json` (modified 2026-09-29) contains A050 and declares next A-falsifier ID `A051`; `catalog_index.json` of the same date does not yet contain A050. A051 therefore ships patch candidates but does not overwrite either index.
