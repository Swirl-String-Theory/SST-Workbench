# Data schema

All numeric energy columns are in **eV** unless stated otherwise. Frequencies are in `rad s^-1`; times in seconds; SI stress/momentum inputs use SI units.

## `modes.csv`

Required columns:

`knot, mode_id, family`

Recommended columns:

- `omega_rad_s`
- `gap_eV` — leave blank if unknown; `0` is allowed for explicitly continuous branches.
- `gap_status` — one of `unknown`, `continuous`, `true_gap`, `discrete`, `activation`.
- `coupling_norm` — preregistered dimensionless coupling proxy.
- `tau_s`
- `degeneracy`
- `independent_energy_channel` — must normally be false for writhe.

Mode families: `translation`, `orientation`, `kelvin`, `twist`, `writhe`, `core`.

## `amplitude_scan.csv`

`knot, mode_id, amplitude, delta_energy_eV`

Use at least 3 small-amplitude points; 5–10 is preferable. Amplitude normalization must be frozen before the scan.

## `encounters.csv`

`knot, mode_id, interaction_id, drive_energy_eV, delta_energy_eV, noise_eV, duration_s`

The empirical transfer fraction is `|delta_energy| / drive_energy`. Significance is estimated as `|delta_energy| / noise_eV`.

## `convergence.csv`

`knot, mode_id, resolution, omega_rad_s, coupling_norm, gap_eV`

The highest two resolutions are compared. A campaign should normally contain more than two resolutions so asymptotic behavior can be inspected rather than inferred from one pair.

## `spectroscopy.csv`

`observable_id, knot, mode_id, lambda_abs, occupation, delta_energy_eV, empirical_limit_eV`

The conservative bound is summed per observable:

`sum |lambda| * p * DeltaE`.

The same mode list must be used as in the mode ledger; do not remove a coupled mode after inspecting the limit.

## `orientation.csv`

`knot, sample_id, tx, ty, tz, weight`

The director is normalized internally. The package computes

`Q = <t t^T> - I/3`

and reports its Frobenius norm.

## `momenta.csv`

`knot, M_kg, cx, cy, cz, weight, number_density_m3`

Here `(cx,cy,cz)` are **peculiar momenta**, not peculiar velocities. The package evaluates

`Pi_ij = n <c_i c_j / M>`.

This is knot-ensemble kinetic stress and is kept separate from `0.5 rho_f v_swirl^2`.

## `energy_ledger.csv`

`interaction_id, knot_pair, delta_E_CM_eV, delta_E_rot_eV, delta_E_kelvin_eV, delta_E_twist_eV, delta_E_core_eV, total_energy_drift_eV, initial_total_energy_eV, delta_Wr`

`delta_Wr` is recorded geometrically and is not added as another energy channel by default.
