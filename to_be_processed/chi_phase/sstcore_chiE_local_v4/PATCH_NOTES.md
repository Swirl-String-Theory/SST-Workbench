# Patch notes: horn-torus chiE integration v4

This local package extends the flat SST ideal-trefoil Biot-Savart package with a reproducible horn-torus closed-loop energy diagnostic and an SSTcore-style C++ API.

## Added / upgraded

- `sst_horn_torus_chiE.py`
  - `HornTorusKernel`
  - `HornTorusParams(rho_sat, Gamma0, a0, lambda_, epsilon, quadrature_n, core_constant)`
  - `HornTorusResult` with `R`, `v0`, `Xi_*`, `chi_*`, `E_loop`, and target residual
  - `evaluate_horn_torus(...)`
  - `scan_lambda(...)`
  - `minimize_lambda(...)`
  - `general_polyline_xi_filament(points, epsilon, a0, cpp_mod)`

- `sst_trefoil_biot.cpp`
  - C++ namespace `sst`
  - `enum class HornTorusKernel`
  - `struct HornTorusParams`
  - `struct HornTorusEnergyResult`
  - `class HornTorusEnergy`
  - pybind bindings for the enum/classes
  - `horn_torus_energy(params, kernel)`
  - `scan_lambda(lambda_min, lambda_max, lambda_count, base, kernel)`
  - `minimize_lambda(lambda_min, lambda_max, base, kernel, iterations=80)`
  - `regularized_neumann_energy_dimensionless_scaled(points, a0, epsilon)`

## Important C++ note

The field is named `lambda_`, not `lambda`, because `lambda` is a C++ keyword and cannot be used as a member name.

## Validated locally

```bash
python test_horn_torus_chiE.py
python simulate_horn_torus_chiE.py --python --lambda-count 5 --n 1024
python sst_trefoil_biot_build.py --force
python simulate_horn_torus_chiE.py --lambda-count 5 --n 4096
python simulate_trefoil_biot_closure.py --python --n 64 --samples 4
```

Observed horn-limit diagnostic for the regularized kernel with `epsilon=1`:

```text
chi_K(lambda=1)        = 7.76096635
chi_cav(lambda=1)      = 9.86960440
chi_E_hollow(lambda=1) = 17.6305708
target 2*pi            = 6.28318531
```

This confirms the intended falsification guard: the simple hollow-core horn model does not falsely reproduce `2*pi`.
