# Wien-Planck SST v0.3.1 PTSA STRICT DIMENSIONLESS BLIND report

Format: `SST-WP-BLIND-ACTION-3.1`

## Gates

- **UA0_no_SST_SI_target_leak**: `True`
- **UA0b_complete_campaign_coverage**: `True`
- **UA1_omega_equals_2pi_f**: `True`
- **UA2_recurrent_mode_prerequisite**: `False`
- **UA2a_frozen_mode_normal_content**: `True`
- **UA2b_normal_relative_equilibrium**: `True`
- **UA2c_positive_resolved_dimensionless_mode_energy**: `False`
- **UA2d_matched_mode_energy_frequency**: `True`
- **UA3_adaptive_mesh_quality**: `False`
- **UA3b_temporal_convergence**: `False`
- **UA4_reject_classical_continuous_action**: `True`
- **UA5_dimensionless_action_amplitude_independence**: `False`
- **UA6_dimensionless_action_universality**: `False`
- **UA7_spatial_convergence**: `False`

## Summary

```json
{
  "classical_continuity_null_triggered": false,
  "coverage_fraction": 1.0,
  "dimensionless_action_cv": null,
  "energy_signal_pass_fraction": 0.0,
  "frozen_mode_pass_fraction": 1.0,
  "highest_resolution_rel_change": null,
  "median_Jf_hat": null,
  "median_Jomega_hat": null,
  "median_action_amplitude_fit_r2": null,
  "median_action_amplitude_log_slope": null,
  "mesh_pass_fraction": 0.16666666666666666,
  "omega_rel_error_max": 0.0,
  "recurrence_pass_fraction": 0.0,
  "relative_equilibrium_pass_fraction": 1.0,
  "resolution_median_Jf_hat": {},
  "temporal_convergence_pass_fraction": 0.16666666666666666
}
```

## Interpretation

The blind verdict concerns only a dimensionless universal-action candidate measured on one frozen, normal-projected mode per carrier/resolution. Energy and frequency are paired on that same mode. Tangential marker motion is excluded from the centerline relative-equilibrium gate. No SI action, canonical normalization, or absolute-target comparison is permitted here.
