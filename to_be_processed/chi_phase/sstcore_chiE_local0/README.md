# SST local Biot-Savart + horn-torus chiE package v3

Compact flat experiment package, extending the existing ideal-trefoil Biot-Savart closure package with a reproducible horn-torus closed-loop \(\chi_E\) diagnostic.

## Files

- `simulate_trefoil_biot_closure.py` — original ideal-trefoil Biot-Savart closure runner and plots.
- `sst_trefoil_biot_py.py` — pure-Python backend: `ideal.txt` parser, Fourier trefoil sampler, SST energy scan.
- `sst_trefoil_biot.cpp` — optional pybind11 C++ backend for Biot-Savart kernels plus horn-torus kernels.
- `sst_trefoil_biot_build.py` — Windows-safe local build/import helper.
- `sst_horn_torus_chiE.py` — new pure-Python horn-torus \(\chi_K,\chi_{\rm cav},\chi_E^{\rm hollow}\) classes and fallback kernels.
- `simulate_horn_torus_chiE.py` — new horn-torus \(\chi_E\) runner, CSV/JSON/PNG exports.
- `test_horn_torus_chiE.py` — dependency-free smoke tests for the horn-torus classes.
- `ideal.txt` — embedded local ideal-knot table; default knot `Id="3:1:1"`.
- `pybind11_headers.zip` — bundled pybind11 headers stored as one file; extracted on first C++ build.
- `requirements.txt` — minimal Python runtime requirements.

The `exports/` folder is created by the runners.

## Status

Research Track numerical infrastructure.  The horn-torus module is a falsification test, not a canonized derivation.  It intentionally separates

\[
\chi_K,
\qquad
\chi_{\rm cav}=\pi^2\lambda,
\qquad
\chi_E^{\rm hollow}=\chi_K+\chi_{\rm cav}.
\]

If cavitation work counts as inertial rest energy, the hollow horn limit \(\lambda=1\) cannot match \(2\pi\), because \(\chi_{\rm cav}(1)=\pi^2>2\pi\) before kinetic energy is added.

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

Optional C++ backend:

```powershell
python simulate_horn_torus_chiE.py --lambda-count 33 --n 32768
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
