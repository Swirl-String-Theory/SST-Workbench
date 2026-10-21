# F005 v0.5.0 - independent linear Euler baseline

**Status:** `BLOCKED_GEOMETRY_UNVERIFIED`

## Gates

- **E0_GEOMETRY**: `BLOCKED`
- **E1_MODAL_SOLVER**: `PASS_ANALYTIC_TESTS_REQUIRED`
- **E2_INPUT_INTEGRITY**: `NOT_RUN`
- **E3_FROM_REST**: `NOT_RUN`
- **E4_CONDITIONAL_ONE_MODE**: `NOT_RUN`
- **E5_BASELINE_COMPARISON**: `NOT_RUN`
- **E6_FAMILY_DISJOINT**: `DEVELOPMENT_PROXY_ONLY`
- **E7_PKLSA**: `NOT_RUN`
- **E8_SST_CLAIMS**: `UNRESOLVED`
- **E9_LINEARIZATION**: `NOT_RUN`

## Blocker
GEOMETRY_UNVERIFIED: missing tank_length_internal_m, tank_width_internal_m, fill_depth_m, sensor_x_from_center_m, liquid_density_kg_m3, surface_tension_N_m, acceleration_axis_sign, measurement_height_sign, geometry_source, sensor_source, orientation_source, fluid_source, initial_equilibrium_source

## Interpretation
No full nonlinear Euler, viscosity, or source-native PKLSA simulation is certified. Geometry inputs are never inferred from ARX/oscillator frequencies. TEST/OOD water-height traces not accessed.
