# SST local Biot-Savart + horn-torus chiE package v5

Compact flat experiment package extending the ideal-trefoil Biot-Savart closure package with a reproducible horn-torus closed-loop \(\chi_E\) diagnostic.

## Files

- `simulate_trefoil_biot_closure.py` — original ideal-trefoil Biot-Savart closure runner and plots.
- `sst_trefoil_biot_py.py` — pure-Python backend: `ideal.txt` parser, Fourier trefoil sampler, SST energy scan.
- `sst_trefoil_biot.cpp` — optional pybind11 C++ backend for Biot-Savart kernels plus C++ horn-torus SSTcore classes.
- `sst_trefoil_biot_build.py` — Windows-safe local build/import helper.
- `sst_horn_torus_chiE.py` — pure-Python horn-torus \(\chi_K,\chi_{\rm cav},\chi_E\) classes and fallback kernels.
- `simulate_horn_torus_chiE.py` — horn-torus \(\chi_E\) runner, CSV/JSON/PNG exports.
- `test_horn_torus_chiE.py` — dependency-free smoke tests for the horn-torus classes.
- `ideal.txt` — embedded local ideal-knot table; default knot `Id="3:1:1"`.
- `pybind11_headers.zip` — bundled pybind11 headers stored as one file; extracted on first C++ build.
- `requirements.txt` — minimal Python runtime requirements.

The `exports/` folder is created by the runners.

## Status

Research Track numerical infrastructure. The horn-torus module is a falsification test, not a canonized derivation. It separates the strict hollow-core hydrodynamic total from possible SST inertial-mass interpretations.

The strict hollow-core factors are

\[
\chi_K,
\qquad
\chi_{\rm cav}=\pi^2\lambda,
\qquad
\chi_E^{\rm hollow}=\chi_K+\chi_{\rm cav}.
\]

If cavitation work counts as inertial rest energy, the hollow horn limit \(\lambda=1\) cannot match \(2\pi\), because \(\chi_{\rm cav}(1)=\pi^2>2\pi\) before kinetic energy is added.

## v5 addition: explicit mass-energy modes

`HornTorusParams` now has a `mass_mode` field.  The selected mass-energy coefficient is reported as `chi_E`; the strict hollow total remains available as `chi_E_hollow` / `chi_E_hollow_total`.

```text
kinetic_only         : chi_E counts only exterior kinetic/Dirichlet energy
kinetic_plus_cavity  : strict hollow-core total, chi_K + chi_cav
vacuum_subtracted    : chi_K with explicit -P_vac V_cav subtraction recorded
target_renormalized  : diagnostic calibrated subtraction needed to force 2*pi
```

In \(\Xi\)-normalization,

\[
\Xi_K=\Xi_{\rm filament},\qquad
\Xi_{\rm cav}=\lambda/4,\qquad
\Xi_{\rm hollow}=\Xi_K+\Xi_{\rm cav}.
\]

The modes select

```text
kinetic_only:         Xi_mass = Xi_K
kinetic_plus_cavity:  Xi_mass = Xi_hollow
vacuum_subtracted:    Xi_mass = Xi_K,      Xi_renormalization = -Xi_cav
target_renormalized:  Xi_mass = 1/(2*pi),  Xi_renormalization = 1/(2*pi) - Xi_hollow
```

`target_renormalized` is intentionally marked as calibrated; it measures the subtraction required to force the old \(\chi_E=2\pi\) normalization.

## C++ / pybind11 API

The C++ backend contains the SSTcore-style API in namespace `sst`:

```cpp
namespace sst {

enum class HornTorusKernel {
    THIN_RING_ASYMPTOTIC,
    REGULARIZED_CIRCULAR_FILAMENT
};

enum class EnergyMassMode {
    KINETIC_ONLY,
    KINETIC_PLUS_CAVITY,
    VACUUM_SUBTRACTED,
    TARGET_RENORMALIZED
};

struct HornTorusParams {
    double rho_sat;
    double Gamma0;
    double a0;
    double lambda_;       // lambda is a C++ keyword
    double epsilon;
    int quadrature_n;
    double core_constant;
    EnergyMassMode mass_mode;
};

struct HornTorusEnergyResult {
    double lambda_;
    double epsilon;
    double R;
    double v0;
    double Xi_filament;
    double Xi_cavitation;
    double Xi_renormalization;
    double Xi_total;      // strict hollow total
    double Xi_mass;       // selected mass-mode value
    double chi_K;
    double chi_cavitation;
    double chi_renormalization;
    double chi_E_hollow_total;
    double chi_E;         // selected mass-mode value
    double E_loop;
    double target_residual;
    std::string mass_mode;
};

class HornTorusEnergy { /* static kernels and evaluate(...) */ };

std::vector<HornTorusEnergyResult> scan_lambda(...);
HornTorusEnergyResult minimize_lambda(...);

}
```

Python bindings expose:

```python
import sst_trefoil_biot as sst

p = sst.HornTorusParams()
p.rho_sat = 1.0
p.Gamma0 = 1.0
p.a0 = 1.0
p.lambda_ = 1.0
p.epsilon = 1.0
p.quadrature_n = 32768
p.core_constant = 1.75
p.mass_mode = sst.EnergyMassMode.VACUUM_SUBTRACTED

r = sst.horn_torus_energy(p, sst.HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT)
print(r.Xi_mass, r.chi_E, r.chi_renormalization, r.target_residual)
```

The pure-Python wrapper `sst_horn_torus_chiE.py` mirrors this API and automatically uses the C++ implementation when a compiled backend is supplied.

## Automatic C++ rebuild behavior

The runners call:

```python
from sst_trefoil_biot_build import import_module
cpp_mod = import_module(auto_build=True, script_dir=SCRIPT_DIR)
```

Before importing `sst_trefoil_biot`, the build helper runs `needs_recompile()`:

```python
if no .pyd/.so exists: rebuild
if sst_trefoil_biot.cpp is newer than the newest .pyd/.so: rebuild
else: import existing extension
```

So editing `sst_trefoil_biot.cpp` and then running either runner triggers a rebuild before the pybindings are imported.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run the horn-torus chiE diagnostic

Pure Python:

```powershell
python simulate_horn_torus_chiE.py --python --lambda-count 9 --n 8192
```

Choose an explicit mass-energy interpretation:

```powershell
python simulate_horn_torus_chiE.py --python --mass-mode kinetic_only
python simulate_horn_torus_chiE.py --python --mass-mode kinetic_plus_cavity
python simulate_horn_torus_chiE.py --python --mass-mode vacuum_subtracted
python simulate_horn_torus_chiE.py --python --mass-mode target_renormalized
```

Optional C++ backend:

```powershell
python simulate_horn_torus_chiE.py --lambda-count 33 --n 32768 --mass-mode vacuum_subtracted
```

Force C++ rebuild:

```powershell
python sst_trefoil_biot_build.py --force
```

Run tests:

```powershell
python test_horn_torus_chiE.py
```

## Run the original trefoil closure scan

```powershell
python simulate_trefoil_biot_closure.py
```

Fast smoke test:

```powershell
python simulate_trefoil_biot_closure.py --n 128 --samples 8
```

## Horn-torus outputs

The horn-torus runner writes:

- `exports/horn_torus_chiE_summary.json`
- `exports/horn_torus_chiE_run_results_summary.txt`
- `exports/horn_torus_chiE_scan.csv`
- `exports/horn_torus_chiE_scan.png`

## Trefoil outputs

The trefoil runner writes:

- `exports/trefoil_biot_summary.json`
- `exports/trefoil_biot_run_results_summary.txt`
- `exports/trefoil_biot_energy_scan.csv`
- `exports/trefoil_biot_energy_scan.png`
- `exports/trefoil_geometry.png`
- `exports/3_1_1_points.xyz`


## v6 diagnostic runs

Three additional reproducibility runs are included:

```powershell
python simulate_epsilon_sweep.py --python --lambda 1.0 --eps-min 0.2 --eps-max 2.0 --eps-count 37 --n 8192
python simulate_mass_mode_comparison.py --python --lambda-min 1 --lambda-max 8 --lambda-count 33 --epsilon 1 --n 8192
python simulate_trefoil_thickness_audit.py --n 384
```

They write:

```text
exports/epsilon_sweep.*
exports/mass_mode_comparison.*
exports/trefoil_thickness_audit.*
exports/trefoil_minrad_values.csv
```

`NEXT_TESTS.md` records the next physical model ladder: hollow-core false result, kinetic/vacuum-subtracted hollow core, solid constant-density core, constant-volume/constant-pressure asymptotic rings, resolved smooth-core profiles, and surface-tension variants.
