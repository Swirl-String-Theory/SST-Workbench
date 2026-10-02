# Changelog

## v0.4.0

- Replaced PTSA-only discovery with self-contained PKLSA v0.1.0: 49 × 48 = 2352 seeds.
- Added SYCL/oneAPI broad-screen backend with deterministic binary geometry protocol.
- Added Stage-1 rigid-invariant pair-strain screening; top 8 per family survive (392).
- Added Stage-2 short RK2 invariant-shape/mesh screening; top 2 per family survive (98).
- Added CPU-double Stage-3 qualification with maximum one final carrier per topology family.
- Added GPU↔CPU parity prerequisite and GPU device/driver/precision provenance.
- Added `UA0c_PKLSA_funnel_preflight` fail-closed gate.
- Preserved v0.3.1 frozen-mode matching, gauge-normal RE, adaptive mesh control and iterative frequency certification.
- Reveal now resolves opaque staged carriers back to PKLSA candidate/family/parameter provenance.
- Added `run_all_cpu_fallback.cmd`; CPU screening is scientifically equivalent as a selection algorithm but much slower and explicitly labelled.
- Output convention remains version-specific with blind-safe share archives and separate revealed archive.

## v0.3.1

See historical release for the iterative-frequency, gauge-normal-RE, adaptive-mesh and frozen-matched-mode corrections.
