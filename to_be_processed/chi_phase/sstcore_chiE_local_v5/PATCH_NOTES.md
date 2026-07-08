# Patch notes: horn-torus chiE integration v5

This local package extends v4 with an explicit `energy_mass_mode` / `mass_mode` switch.  The goal is to separate the strict hollow-core hydrodynamic total from possible SST inertial-mass interpretations.

## New in v5

### Python API

`sst_horn_torus_chiE.py` now adds:

- `EnergyMassMode`
  - `KINETIC_ONLY`
  - `KINETIC_PLUS_CAVITY`
  - `VACUUM_SUBTRACTED`
  - `TARGET_RENORMALIZED`
- `HornTorusParams(..., mass_mode="kinetic_plus_cavity")`
- `HornTorusResult` fields:
  - `Xi_renormalization`
  - `Xi_mass`
  - `chi_renormalization`
  - `chi_E_hollow_total`
  - `mass_mode`
- `evaluate_horn_torus(..., mass_mode=...)`
- `scan_lambda(..., mass_mode=...)`
- `minimize_lambda(..., mass_mode=...)`

The v4 fields remain valid.  In particular, `chi_E_hollow` remains available as a backward-compatible property for the strict hollow total.

### C++ / pybind11 API

`sst_trefoil_biot.cpp` now adds the C++ enum:

```cpp
namespace sst {

enum class EnergyMassMode {
    KINETIC_ONLY,
    KINETIC_PLUS_CAVITY,
    VACUUM_SUBTRACTED,
    TARGET_RENORMALIZED
};

}
```

`HornTorusParams` now has:

```cpp
EnergyMassMode mass_mode = EnergyMassMode::KINETIC_PLUS_CAVITY;
```

`HornTorusEnergyResult` now reports:

```cpp
double Xi_renormalization;
double Xi_mass;
double chi_renormalization;
double chi_E_hollow_total;
std::string mass_mode;
```

The selected `chi_E` is now the selected mass-mode value.  The strict hollow value remains available as `chi_E_hollow_total`.

## Mass-mode definitions

Let

```text
Xi_K      = Xi_filament
Xi_cav    = lambda/4
Xi_hollow = Xi_K + Xi_cav
Xi_target = 1/(2*pi)
```

Then:

```text
kinetic_only:         Xi_mass = Xi_K
kinetic_plus_cavity:  Xi_mass = Xi_hollow
vacuum_subtracted:    Xi_mass = Xi_K,      Xi_renormalization = -Xi_cav
target_renormalized:  Xi_mass = Xi_target, Xi_renormalization = Xi_target - Xi_hollow
```

`target_renormalized` is not a derivation. It is a diagnostic that measures the calibrated subtraction needed to force `chi_E=2*pi`.

## CLI examples

Strict hollow-core total:

```bash
python simulate_horn_torus_chiE.py --python --lambda-count 5 --n 1024 --mass-mode kinetic_plus_cavity
```

Vacuum-subtracted/excess mode:

```bash
python simulate_horn_torus_chiE.py --python --lambda-count 5 --n 1024 --mass-mode vacuum_subtracted
```

Diagnostic calibrated target mode:

```bash
python simulate_horn_torus_chiE.py --python --lambda-count 5 --n 1024 --mass-mode target_renormalized
```

## Validated locally

```bash
python test_horn_torus_chiE.py
python simulate_horn_torus_chiE.py --python --lambda-count 5 --n 1024
python simulate_horn_torus_chiE.py --python --lambda-count 5 --n 1024 --mass-mode vacuum_subtracted
python simulate_horn_torus_chiE.py --python --lambda-count 5 --n 1024 --mass-mode target_renormalized
python sst_trefoil_biot_build.py --force
python simulate_horn_torus_chiE.py --lambda-count 5 --n 4096 --mass-mode vacuum_subtracted
```

Observed horn-limit diagnostic for the regularized kernel with `epsilon=1`:

```text
strict hollow total:
  chi_K(lambda=1)        = 7.76096635
  chi_cav(lambda=1)      = 9.86960440
  chi_E_hollow(lambda=1) = 17.6305708

vacuum-subtracted:
  chi_renormalization    = -9.86960440
  chi_E_selected         = 7.76096635

target-renormalized:
  chi_renormalization    = -11.34738544
  chi_E_selected         = 6.28318531
```

This makes the open SST choice explicit: does inertial rest mass count cavity work, subtract vacuum work, or require a resolved-core/renormalized energy functional?
