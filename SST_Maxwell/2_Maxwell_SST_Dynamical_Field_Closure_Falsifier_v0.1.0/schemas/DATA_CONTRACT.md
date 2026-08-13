# Data contract

Each campaign directory contains three compressed NumPy files. Every file contains a scalar UTF-8 JSON string `meta_json` plus the arrays below. Complex arrays are native NumPy complex arrays.

## `transverse.npz`

Required arrays: `kvec[N,3]`, `omega[N]`, `Avec[N,3]`. Optional: `mode_power[N]`, `E_kin[N]`, `E_el[N]`.

Required metadata declarations, all literally `false`: `projector_applied`, `gauge_reduced_input`, `divergence_constraint_enforced`. A calculation violating these declarations is **INVALID**, not a failure or pass.

`Avec` must be taken from the unreduced eigensystem or unreduced Fourier field. Zero-frequency longitudinal coordinates are allowed; the gate rejects a finite-frequency longitudinal radiative branch.

## `displacement.npz`

Required arrays: `kvec[N,3]`, `omega[N]`, `xi[N,3]`, `P[N,3]`, `J[N,3]`, `rho_bound[N]`.

Required metadata declarations, all literally `true`: `xi_independent`, `P_independent`, `J_independent`, `rho_bound_independent`.

These declarations mean the four channels were reconstructed independently from the underlying solver or measurement. Do not create `J` and `rho_bound` algebraically from the same stored `P` and then claim an independent closure test.

Fourier sign convention is `exp(i(k·x - omega t))`, hence `J = -i omega P` and `rho_bound = -i k·P`.

## `gravity.npz`

Required arrays: `d[N]`, `E_total[N]`, `F_independent[N]`, scalar `E_infinity[1]`, `rho_E_min[N]`, `rho_E_scale[N]`.

Required metadata declarations, all literally `true`: `same_hamiltonian`, `fully_relaxed`, `force_independent`.

`F_independent` must come from surface stress, momentum flux, constraint force, or another declared force channel that does **not** numerically differentiate `E_total`. Increasing `d` is the positive outward direction, so attraction is negative force.

`E_infinity` is the separately computed noninteracting reference using the same Hamiltonian and numerical conventions. `rho_E_min` is the minimum *absolute* energy density sampled for each state, while `rho_E_scale` is a positive representative energy-density scale used only for the roundoff tolerance.
