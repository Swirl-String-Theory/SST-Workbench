# Patch notes: horn-torus chiE integration

This local package extends the existing flat SST ideal-trefoil Biot-Savart package with a reproducible horn-torus closed-loop energy diagnostic.

## Added

- `sst_horn_torus_chiE.py`
  - `HornTorusParams`
  - `HornTorusResult`
  - `PrimitiveScales`
  - `evaluate_horn_torus(...)`
  - `scan_lambda(...)`
  - `xi_regularized_circular_filament(...)`
  - `xi_thin_ring(...)`
  - `xi_cavitation(...)`
  - `general_polyline_xi_filament(...)`

- `simulate_horn_torus_chiE.py`
  - produces JSON, CSV, PNG, and text exports.

- `test_horn_torus_chiE.py`
  - dependency-free smoke tests.

## Modified

- `sst_trefoil_biot.cpp`
  - added C++/pybind functions:
    - `horn_xi_cavitation(lambda_)`
    - `horn_chi_from_xi(xi)`
    - `horn_xi_thin_ring(lambda_, core_constant)`
    - `horn_xi_regularized_filament(lambda_, epsilon, quadrature_n)`
    - `horn_chi_K_regularized(lambda_, epsilon, quadrature_n)`
    - `regularized_neumann_energy_dimensionless(points, epsilon)`

- `README.md`
  - updated run instructions and status guard.

## Validated locally

```bash
python test_horn_torus_chiE.py
python simulate_horn_torus_chiE.py --python --lambda-count 5 --n 4096
python sst_trefoil_biot_build.py --force
python simulate_horn_torus_chiE.py --lambda-count 5 --n 4096
python simulate_trefoil_biot_closure.py --python --n 64 --samples 4
```

Observed horn-limit diagnostic for the regularized kernel with `epsilon=1`:

```text
chi_K(lambda=1)       = 7.76096635
chi_cav(lambda=1)     = 9.86960440
chi_E_hollow(lambda=1)= 17.6305708
target 2*pi           = 6.28318531
```

This confirms the intended falsification guard: the simple hollow-core horn model does not falsely reproduce `2*pi`.
