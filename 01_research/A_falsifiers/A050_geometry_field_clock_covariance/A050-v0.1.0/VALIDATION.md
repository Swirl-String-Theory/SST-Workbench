# Validation gates

1. **Blind provenance:** blind configuration contains only dimensionless numerical controls and generated geometry IDs.
2. **Discrete incompressibility:** projected vector-field divergence RMS divided by gradient RMS must be below `1e-10`.
3. **Nonzero closure:** the scalar closure variance must be finite and positive.
4. **Scaling quality:** the scalar finite-volume variance fit must meet `power_fit_r2_min`.
5. **Null separation:** the shuffled-null exponent minus the scalar-closure exponent must be at least `null_gap_min` for a family to qualify.
6. **Cross-family requirement:** at least two families must qualify for `CORRELATED_CLOSURE_SCALING_DETECTED`.
7. **Resolution gate:** the preregistered resolution check must remain within `max_exponent_delta`.
8. **No physical calibration in the blind verdict:** absolute clock units and theory-specific target values are excluded.

The temporal fit is diagnostic in v0.1.0 and does not control the primary verdict.
