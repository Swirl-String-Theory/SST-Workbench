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

## v6 additions

Added three reproducible diagnostic runs requested for Step-2 validation:

1. `simulate_epsilon_sweep.py` — sweeps the regularization/softening radius `epsilon` at fixed horn parameter `lambda`.
2. `simulate_mass_mode_comparison.py` — compares kinetic-only, strict hollow-core, vacuum-subtracted, and target-renormalized mass-energy interpretations.
3. `simulate_trefoil_thickness_audit.py` — adds a trefoil geometry/thickness proxy audit using segment-segment distance, MinRad, and diameter/radius-normalized ropelength estimates.

Added `NEXT_TESTS.md` with the post-hollow-core roadmap:

- hollow-core positive cavity result as a falsified/simple model;
- kinetic-only/vacuum-subtracted hollow model;
- solid constant-density core;
- constant-volume vs constant-pressure ring asymptotics;
- smooth resolved-core density profile;
- surface tension contribution;
- future boundary-element exterior Dirichlet/Neumann solve.

The package is cleaned for cross-platform rebuild: generated Windows `.pyd`, build folders, `_pybind11_include`, and `__pycache__` are excluded from the v6 zip.

## v7 additions

Added the next Step-2 test requested after the hollow-core falsification:

- `sst_solid_core_chiE.py` — pure-Python solid-core / constant-density Rankine-core chiE model.
- `simulate_solid_core_constant_density.py` — reproducible runner for the solid-core constant-density test.
- `test_solid_core_constant_density.py` — dependency-free tests for the new model.

The model removes positive cavitation work and replaces it with internal kinetic energy of a constant-density Rankine tube:

\[
 v_\theta(s)=\frac{\Gamma_0}{2\pi a_0^2}s,\qquad 0\le s\le a_0.
\]

The toroidal internal energy is

\[
 E_{\rm int}=\frac{\rho_{\rm sat}\Gamma_0^2 R}{8},
\qquad
 \Xi_{\rm int}=\frac{\lambda}{8},
\qquad
 \chi_{\rm int}=\frac{\pi^2\lambda}{2}.
\]

The first asymptotic total test uses the classic solid-core + constant-volume thin-ring constant

\[
 \alpha_E=\frac74,
\]

with

\[
 E\simeq\frac12\rho\Gamma^2R
 \left[\log\left(\frac{8R}{a}\right)-\alpha_E\right],
\]

or dimensionlessly

\[
 \Xi_E^{\rm solid}(\lambda)
 =\frac12\lambda\,[\log(8\lambda)-\alpha_E],
 \qquad
 \chi_E=4\pi^2\Xi_E.
\]

Important guard: this is a thin-ring asymptotic formula.  Evaluating it at the horn threshold \(\lambda=1\) is a diagnostic extrapolation, not a finite-core derivation.

Validated locally:

```bash
python test_horn_torus_chiE.py
python test_solid_core_constant_density.py
python simulate_solid_core_constant_density.py --lambda-count 9 --alpha-count 11
```

---

## v7 merge note: bulk matrix + preserved v6 exports

This v7 artifact was merged using the user-uploaded `sstcore_chiE_local_v7.zip` as base. Existing v7 source files were preserved. The following were added without removing existing files:

- `run_chiE_bulk_matrix.py`
- `V5_MERGE_AUDIT.md`
- `USER_V6_EXPORTS_AUDIT.md`
- preserved export directories for v6/reference comparison.

The artifact remains named `sstcore_chiE_local_v7.zip`.
