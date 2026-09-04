# SYCL worker architecture (GPU audit template)

## Why

On Windows with oneAPI 2026.x, pybind `.pyd` modules that contain real SYCL **device** kernels can terminate CPython during import (`0xC0000005`), before any queue or Biot-Savart call. Bind-only `-fsycl` modules often import fine.

## Isolation

This template never imports SYCL device code into CPython:

- `_native.pyd` is **host / OpenMP only**
- GPU work runs in `build/sst_sycl_worker.exe` (standalone DPC++)
- Python keeps one persistent child process and exchanges compact binary arrays over stdin/stdout
- The same SYCL queue is reused for the process lifetime

## Precision

The worker probes `sycl::aspect::fp64`. If native FP64 exists, computation uses double. If not (Intel Arc A770), FP32 is disabled unless `SST_SYCL_ALLOW_FP32=1` is set. Such output is **screening FP32**, not confirmatory near-threshold evidence.

## Commands

- `run_sycl_worker_smoke.cmd` — build, device probe, persistent worker smoke, FP32-vs-host-FP64 velocity parity (`rel L2 < 5e-4`)
- `run_arc.cmd` / `run_all.cmd` — session oneAPI env + full audit battery using the external worker for `backend=sycl`
