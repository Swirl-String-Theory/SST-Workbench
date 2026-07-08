# SST ideal-trefoil Biot-Savart closure package v2

Compact flat experiment package, matching the style of `sst_chi_phase_package_v6` while keeping the source folder under 10 top-level files.

## Files

- `simulate_trefoil_biot_closure.py` — main runner and plots.
- `sst_trefoil_biot_py.py` — pure-Python backend: `ideal.txt` parser, Fourier trefoil sampler, SST energy scan.
- `sst_trefoil_biot.cpp` — optional pybind11 C++ backend for Biot-Savart kernels.
- `sst_trefoil_biot_build.py` — Windows-safe local build/import helper.
- `ideal.txt` — embedded local ideal-knot table; default knot `Id="3:1:1"`.
- `pybind11_headers.zip` — bundled pybind11 headers stored as one file; extracted on first C++ build.
- `requirements.txt` — minimal Python runtime requirements.

The `exports/` folder is created by the runner.

## Automatic C++ rebuild behavior

Yes. The main runner calls:

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

So editing `sst_trefoil_biot.cpp` and then running `simulate_trefoil_biot_closure.py` triggers a rebuild before the pybindings are imported.

## Run

```powershell
python -m pip install -r requirements.txt
python simulate_trefoil_biot_closure.py
```

Force pure Python:

```powershell
python simulate_trefoil_biot_closure.py --python
```

Force C++ rebuild:

```powershell
python sst_trefoil_biot_build.py --force
```

Fast smoke test:

```powershell
python simulate_trefoil_biot_closure.py --n 128 --samples 8
```

## Outputs

The runner writes:

- `exports/trefoil_biot_summary.json`
- `exports/trefoil_biot_run_results_summary.txt`
- `exports/trefoil_biot_energy_scan.csv`
- `exports/trefoil_biot_energy_scan.png`
- `exports/trefoil_geometry.png`
- `exports/3_1_1_points.xyz`

## Status

Research Track numerical infrastructure. It computes a local ideal-trefoil Biot-Savart closure scan using the embedded `ideal.txt` geometry and SST constants. It is not a derivation that SST/Euler/NLSE dynamically selects the reported radius.
