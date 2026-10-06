# Validation

The package is designed around four separable validation layers.

1. **Source provenance.**  The selected E011 seed must be `STATIC_READY`, have
   topology `3_1`, and carry a resolvable source locator.  v0.1.0 accepts the
   `gilbert_ab_record` provider anchor because it preserves the same AB representation
   already supported by C006.

2. **Backend provenance.**  C006-v0.3.0 is imported from the user's existing
   SST-Workbench.  E012 records SHA-256 hashes of the C006 modules actually used
   (`dynamics.py`, `geometry.py`, `backend.py`, `spectral_cert.py`) where available.

3. **Numerical convergence.**  Each mode is recomputed over the frozen C006
   N-ladder.  Full spectra are tracked with C006 Hungarian matching and the selected
   positive-frequency branch is separately tested for relative frequency shift.

4. **Physical handoff.**  Dimensionless branch success is not sufficient for A052.
   SI k, omega and energy mapping are emitted only from an explicitly approved,
   independent `configs/physical_scale.json`.

A missing physical scale is a scientific BLOCK, not a software failure.

## Release software checks

- Unit tests: **6/6 PASS**.
- Python compile check: **PASS**.
- End-to-end synthetic smoke: **PASS as a software-path test**. The synthetic
  trefoil fixture deliberately did not satisfy the dynamic convergence gates, so no
  physical/A052 candidate was emitted. This fixture is not scientific evidence.
- No scientific outputs are bundled with the source release; the canonical campaign
  must be executed against the user's SST-Workbench E011/C006 sources.
