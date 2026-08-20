# SST GPU SYCL/DPC++ audit template (GPU-first, external worker)

Copy-rename starter for SST Workbench audits that should run **on Intel Arc** (Level Zero / DPC++), not on host OpenMP.

- Hot path: regularized Biot-Savart on GPU via **out-of-process** `build/sst_sycl_worker.exe`
- Host `.pyd`: OpenMP / serial only (no SYCL device kernels in CPython — avoids Windows import `0xC0000005`)
- Smoke: `vec_add` / `min_abs` on host; GPU smoke via `run_sycl_worker_smoke.cmd`
- Fallbacks: MSVC `/openmp`, then Python (tiny sizes only)

See [`docs/SYCL_WORKER_ARCHITECTURE.md`](docs/SYCL_WORKER_ARCHITECTURE.md).

The CPU sibling remains [`../SST_cpp_pybind_audit_template`](../SST_cpp_pybind_audit_template).

## Requirements / hardware

- **Intel oneAPI** (DPC++ / `icpx`, Level Zero) must be installed
- Target GPU: **Intel Arc A770 16 GB** (`ONEAPI_DEVICE_SELECTOR=level_zero:gpu`)
- Arc has **no native fp64**: set `SST_SYCL_ALLOW_FP32=1` for screening runs; results are FP32-vs-host-FP64, not confirmatory near-threshold evidence
- No permanent Windows PATH: launchers use `setlocal` + session `setvars.bat`
- NVIDIA/CUDA is **not** a fallback here (separate future template)

## Layout

```
SST_GPU_SYCL_DPC_audit_template/
├── run_install.cmd
├── run_sycl_worker_smoke.cmd   # proven Arc smoke (mirror MultiTopology v0.4.5)
├── run_arc.cmd                 # setvars + worker smoke + full checks
├── run_all.cmd                 # install + run_arc.cmd
├── cpp/native.cpp              # host/OpenMP pybind only
├── cpp/sycl_worker.cpp         # standalone DPC++ worker
├── native_ext/sycl_worker.py
├── tools/build_sycl_worker.py
├── tools/sycl_worker_smoke.py
└── docs/SYCL_WORKER_ARCHITECTURE.md
```

Outputs: `{folder_name}_outputs/` inside the package.

## Quick start (Arc A770)

```bat
cd templates\SST_GPU_SYCL_DPC_audit_template
run_all.cmd
```

Or smoke only:

```bat
run_sycl_worker_smoke.cmd
```

Expect worker `is_gpu=true`, backend `sycl-worker-fp32` on Arc, relative L2 vs Python FP64 `< 5e-4`.

Heavy Biot-Savart:

```bat
set SST_SYCL_ALLOW_FP32=1
python run_example.py --n-segments 512 --n-queries 8192 --backend sycl --summary-only
```

Without Arc:

```bash
python run_example.py --tiny --backend python
python -m pytest -q
python run_all_checks.py --force-python
```

## Backend ladder

1. External SYCL worker GPU (`level_zero:gpu`) — preferred
2. Host OpenMP `.pyd`
3. Python — tiny sizes only

Env: `SST_BACKEND`, `SST_SYCL_ALLOW_FP32`, `SST_DISABLE_OPENMP`, `ONEAPI_DEVICE_SELECTOR`, `SYCL_CACHE_PERSISTENT=0`.

## Replace the kernel

1. Keep host OpenMP formula in `cpp/native.cpp` / `fallback.py`
2. Mirror the GPU loop in `cpp/sycl_worker.cpp` (`parallel_for` over query index M)
3. Keep the binary IPC protocol in `native_ext/sycl_worker.py` unless you extend commands

## Tests

```bash
python -m pytest -q
```

`test_sycl_worker_heavy_or_skip` skips without a worker GPU; on Arc it requires `sycl-worker-*` and `is_gpu=true`.

## Dependencies

- Python 3.10+
- `numpy`, `pybind11`, `setuptools`, `pytest`
- Intel oneAPI DPC++ + Arc A770 driver
- Visual Studio 2022 for OpenMP host `.pyd`
