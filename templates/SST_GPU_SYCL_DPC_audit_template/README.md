# SST GPU SYCL/DPC++ audit template (GPU-first)

Copy-rename starter for SST Workbench audits that should run **on Intel Arc** (Level Zero / DPC++), not on host OpenMP.

- Hot path: regularized Biot-Savart, `sycl::parallel_for` over query index `M`
- Smoke: `vec_add`
- CPU lesson: `min_abs` with OpenMP 2.0 thread-local min (no `reduction(min:)` — MSVC C7660)
- Fallbacks: MSVC `/openmp`, then Python (tiny sizes only)

This is **not** Whisper / `SSTcore_TTS` / OpenVINO. Compile with `icpx -fsycl` and load the `.pyd` in the same Python that built it.

The CPU sibling remains [`../SST_cpp_pybind_audit_template`](../SST_cpp_pybind_audit_template).

## Layout

```
SST_GPU_SYCL_DPC_audit_template/
├── README.md
├── run_arc.cmd               # oneAPI setvars + Level Zero + GPU-only checks
├── run_example.py            # default: biot_savart N=512 M=8192
├── run_sweep.py              # scale M
├── run_all_checks.py
├── cpp/native.cpp
├── cpp/list_sycl_devices.cpp
├── native_ext/
└── tests/
```

After copying, edit `native_ext/_config.py`, then replace `biot_savart` in `cpp/native.cpp` **without** removing the persistent `sycl::queue` (`g_queue`). Keep the O(M×N) loop inside `parallel_for`. OpenMP is a laptop fallback, not the target architecture.

## Quick start (Arc)

```bat
cd templates\SST_GPU_SYCL_DPC_audit_template
pip install -r requirements.txt
run_arc.cmd
```

`run_arc.cmd` loads Intel oneAPI `setvars.bat`, sets `ONEAPI_DEVICE_SELECTOR=level_zero:0`, probes devices, then `python run_all_checks.py --force-build --backend sycl`. It **exits nonzero** if there is no GPU so you do not silently run on CPU.

Without Arc:

```bash
python run_example.py --tiny --backend python
python -m pytest -q
python run_all_checks.py --force-python --out-dir audit_out
```

## Backend ladder

1. SYCL GPU (`gpu_selector_v` / Level Zero) — always preferred
2. SYCL CPU only with `--allow-sycl-cpu`
3. MSVC `/openmp` (not `/openmp:llvm`)
4. Python — warn on large M×N

`--backend auto|sycl|openmp|python`. Environment: `SST_BACKEND`, `SST_DISABLE_SYCL=1`, `SST_DISABLE_OPENMP=1`.

## Replace the kernel

`biot_savart` is the stand-in for your filament kernel (Einstein-style regularized midpoint velocity, no 3×3 gradient). To swap:

1. Keep `queue_state()` / `g_queue` process-lifetime.
2. Put the outer index in `h.parallel_for(sycl::range<1>(M), ...)`.
3. Keep a host OpenMP loop over the same index for `--backend openmp`.
4. Mirror the formula in `native_ext/fallback.py` for parity tests.

Per-call `sycl::buffer`s sit on that queue. For a sticky filament, switch the points array to `sycl::malloc_device` and reuse it across query batches.

## C++ rebuild

`build_ext_if_needed.py` hashes `cpp/native.cpp`. It tries `icpx -fsycl -DSST_HAVE_SYCL` first, then setuptools/MSVC `/openmp`.

```bash
python -m native_ext.build_ext_if_needed --force
python run_example.py --tiny
python run_example.py --n-segments 512 --n-queries 8192 --backend auto --summary-only
```

## CLI

### `run_example.py`

| Flag | Default | Meaning |
|------|---------|---------|
| `--tiny` | off | `vec_add` smoke |
| `--n-segments` | 512 | filament N |
| `--n-queries` | 8192 | query M |
| `--backend` | auto | auto/sycl/openmp/python |
| `--allow-sycl-cpu` | off | SYCL CPU if no GPU |
| `--force-python` | off | skip native |
| `--force-build` | off | ignore stamp |
| `--out` | — | JSON path |
| `--summary-only` | off | one-line PASS/FAIL |

### `run_sweep.py`

Scales `--queries` (M), not two scalars. Default `1024,4096,8192` with `--n-segments 256`.

### `run_all_checks.py`

Writes `smoke_python.json`, `smoke_openmp.json`, `smoke_sycl.json`, optional `heavy_sycl.json` (N=512,M=8192 on GPU), `sweep.csv`, `audit_summary.json` with timings.

## Tests

```bash
python -m pytest -q
```

Python tests always run. Native parity skips if the extension did not build. `test_sycl_heavy_or_skip` skips without a SYCL GPU; on Arc it requires `backend=sycl` and `is_gpu=true`.

## Dependencies

- Python 3.10+
- `numpy`, `pybind11`, `setuptools`, `pytest`
- Intel oneAPI DPC++ (`icpx`) + Arc driver for the GPU path
- Visual Studio 2022 for the OpenMP fallback (`/openmp` only)
