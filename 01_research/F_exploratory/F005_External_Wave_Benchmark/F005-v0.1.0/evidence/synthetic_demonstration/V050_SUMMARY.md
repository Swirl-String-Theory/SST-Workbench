# F005 v0.5.0 - independent linear Euler baseline

**Status:** `DEMO_SYNTHETIC_NOT_EXPERIMENT`

## Gates

- **E0_GEOMETRY**: `DEMO_ONLY`
- **E1_MODAL_SOLVER**: `PASS_SYNTHETIC`
- **E2_INPUT_INTEGRITY**: `SYNTHETIC`
- **E3_FROM_REST**: `NOT_RUN`
- **E4_CONDITIONAL_ONE_MODE**: `NOT_RUN`
- **E5_BASELINE_COMPARISON**: `NOT_RUN`
- **E6_FAMILY_DISJOINT**: `DEVELOPMENT_PROXY_ONLY`
- **E7_PKLSA**: `NOT_RUN`
- **E8_SST_CLAIMS**: `UNRESOLVED`
- **E9_LINEARIZATION**: `NOT_RUN`

## Blocker
None; see provenance and science contract.

## Interpretation
No full nonlinear Euler, viscosity, or source-native PKLSA simulation is certified. Geometry inputs are never inferred from ARX/oscillator frequencies. TEST/OOD water-height traces not accessed.
