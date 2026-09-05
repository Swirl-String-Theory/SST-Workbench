# Input formats — v0.3.1

## Geometry dataset

The campaign accepts the same supported XYZ/KnotPlot-compatible centerline sources
as v0.2.0. Multi-component sources remain separate components.

## Blind raw observation schema

Generated internally; users should not hand-author the scientific campaign output.

Core numerical columns include:

```text
amplitude_hat
delta_E_hat
base_energy_hat
delta_E_over_abs_base
energy_signal_valid
frequency_hat
omega_hat
spectral_power
cycles
period_cv
harmonic_r2
epsilon_RE
mesh_cv_plus
mesh_cv_minus
dt_hat_min
dt_hat_max
resolution_N
normalization_L_hat
normalization_Gamma_hat
core_fraction_hat
```

Identity-bearing fields are quarantined before the blind scorer runs.

The blind scorer rejects SI action/frequency column names such as
`delta_E_J` or `frequency_Hz`.

## Reveal-only independent normalization

```json
{
  "rho_kg_m3": 0.0,
  "Gamma_m2_s": 0.0,
  "L_m": 0.0,
  "independent_of_Planck_chain": true,
  "provenance_note": "Independent derivation/measurement details.",
  "target_relative_tolerance": 0.05
}
```

The boolean is a declaration, not proof; the provenance note must be audited.
