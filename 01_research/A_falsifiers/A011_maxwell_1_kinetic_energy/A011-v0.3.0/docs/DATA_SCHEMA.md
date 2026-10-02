# Data schema — v0.3.0

All energy columns are in **eV** unless explicitly marked `J`.  Frequencies are `rad s^-1`; times are seconds; stresses and forces are SI.

## Existing Maxwell kinetic tables

### `modes.csv`

Required: `knot,mode_id,family`.

Recommended: `omega_rad_s,gap_eV,gap_status,coupling_norm,tau_s,degeneracy,independent_energy_channel`.

Mode families: `translation,orientation,kelvin,twist,writhe,core`.

### `amplitude_scan.csv`

`knot,mode_id,amplitude,delta_energy_eV`

### `encounters.csv`

`knot,mode_id,interaction_id,drive_energy_eV,delta_energy_eV,noise_eV,duration_s`

### `convergence.csv`

`knot,mode_id,resolution,omega_rad_s,coupling_norm,gap_eV`

### `spectroscopy.csv`

`observable_id,knot,mode_id,lambda_abs,occupation,delta_energy_eV,empirical_limit_eV`

### `orientation.csv`

`knot,sample_id,tx,ty,tz,weight`

### `momenta.csv`

`knot,M_kg,cx,cy,cz,weight,number_density_m3`

`(cx,cy,cz)` are peculiar **momenta**.  The package evaluates

`Pi_ij = n <c_i c_j/M>`.

### `energy_ledger.csv`

`interaction_id,knot_pair,delta_E_CM_eV,delta_E_rot_eV,delta_E_kelvin_eV,delta_E_twist_eV,delta_E_core_eV,total_energy_drift_eV,initial_total_energy_eV,delta_Wr`

`delta_Wr` is geometric and is not added as an independent energy channel by default.

---

# New Boltzmann / Verlinde tables

## `state_distribution.csv`

`macrostate_id,ensemble_id,observed,knot,invariant_sector,position_bin,energy_bin,energy_eV,occupation,degeneracy`

- `macrostate_id` groups candidate state distributions that share fixed macroscopic constraints.
- exactly one candidate should have `observed=true` when testing maximum permutability.
- `occupation` must be a non-negative integer count for the combinatorial `N!/prod w_i!` audit.
- `degeneracy` defaults to 1.
- `invariant_sector` is mandatory in a serious physical campaign even though an empty string is syntactically accepted.

## `state_occupations.csv`

`ensemble_id,knot,invariant_sector,state_id,energy_eV,occupation,degeneracy`

Used to fit

`ln(occupation/degeneracy) = const - E/(kBT)`.

At least three positive-occupation states and at least two distinct energies are needed.

## `state_counts.csv`

`series_id,knot,invariant_sector,x_m,energy_eV,state_count,log_state_count,T_eff_K`

Supply either:

- `state_count > 0`, or
- `log_state_count` directly for huge multiplicities.

`log_state_count` takes precedence.  At least three positions at fixed energy are needed for `dS/dx`; at least three energies at fixed position are needed for the microcanonical-temperature regression.

## `detailed_balance.csv`

`transition_id,knot,E_i_eV,E_j_eV,g_i,g_j,count_i_to_j,count_j_to_i`

Counts must be proportional to transition rates under equal preregistered exposure.  The optional guard tests

`k_ij/k_ji = (g_j/g_i) exp[-(E_j-E_i)/(kBT)]`.

## `force_reference.csv`

`series_id,x_m,hyd_force_N,probe_mass_kg,pressure_gradient_Pa_per_m`

Preferred: provide `hyd_force_N` from an independent force/stress integration.

Fallback: when `hyd_force_N` is blank and both remaining physical columns are supplied, the package evaluates

`F_hyd = -(probe_mass_kg/rho_f) * pressure_gradient_Pa_per_m`.

## `integrability.csv`

`sample_id,gradT_x_K_per_m,gradT_y_K_per_m,gradT_z_K_per_m,gradp_x_Pa_per_m,gradp_y_Pa_per_m,gradp_z_Pa_per_m`

Tests the normalized cross product of `grad(T)` and `grad(p)`.

## `screens.csv`

`screen_series_id,radius_m,area_m2,bits_N,energy_J,T_K`

`area_m2` may be blank when `radius_m` is present; a spherical area `4*pi*r^2` is then used.  Tests area scaling, inferred `G`, and equipartition.

## `entropy_displacement.csv`

`sample_id,probe_mass_kg,dSdx_J_per_K_m`

Optional Verlinde postulate comparison.

## `radial_force.csv`

`series_id,radius_m,observed_force_N`

At least three radii.  The fitted log-log slope is compared with `-2`.

## `potential_entropy.csv`

`sample_id,deltaPhi_m2_s2,deltaS_per_bit_J_per_K`

Optional comparison with `DeltaS/n = -k_B DeltaPhi/(2c^2)`.
