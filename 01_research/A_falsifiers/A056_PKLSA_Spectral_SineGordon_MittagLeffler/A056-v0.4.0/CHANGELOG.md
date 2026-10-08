# Changelog

## v0.4.0 - circular/Fourier spectral preregistration

- Rebased the A056 instance on SST Falsifier Framework v1.0.6 CANONICAL_FROZEN.
- Replaced the v0.3.0 raw-phase split-POD **blocking** criterion with `circular_fourier_v1`.
- Added circular embedding `z=exp(i phi)`, per-time spatial-mean removal, top-three circular-POD energy/orthogonality metrics, and discovery/confirmation normalized non-zero Fourier-power overlap.
- Frozen blocking thresholds before any official v0.4.0 provider run: circular top-three energy `>=0.95`, circular orthogonality residual `<=1e-10`, Fourier-power overlap `>=0.90`.
- Retained raw-phase split-POD overlap and circular early/late POD overlap as diagnostics only.
- Marked all observed v0.3.0 `m=3` real-filament cases development-only for v0.4.0.
- Preregistered fresh real-provider Kelvin perturbation `m=4`, `epsilon=0.03`.
- Preserved the v0.3.0 ringdown observable and all SG/ML discovery, holdout, certification and evidence-class thresholds.
- Migrated launch/bootstrap/reveal orchestration to the canonical v1.0.6 framework contract.
- Added read-only v0.3.0 development reanalysis and v0.4.0 invariant spectral diagnostic tooling.
