# v0.4.4 SYCL worker architecture

## Why
On Windows/Python 3.14 with oneAPI 2026.x, staged diagnostics showed that pybind modules compiled with `-fsycl` but **without a device kernel** import normally, whereas `.pyd` modules containing a real SYCL device kernel terminate CPython during DLL/module loading with `0xC0000005`. The crash occurs before queue creation or Biot--Savart execution.

## Isolation
v0.4.4 therefore never imports SYCL device code into CPython. `_native.pyd` is host/OpenMP only. GPU work runs in `build/sst_sycl_worker_<hash>.exe`, a standalone DPC++ executable. Python maintains one persistent child process and exchanges compact binary arrays over stdin/stdout. The same queue is reused over the whole campaign.

## Precision
The worker probes `sycl::aspect::fp64`. If native FP64 exists, worker computation uses double. If it does not (e.g. Arc A770), FP32 is disabled unless `SST_SYCL_ALLOW_FP32=1` is explicitly set. Such output is labeled `screening_fp32_only`; it is not confirmatory evidence for near-threshold gate decisions, RPO recurrence, or Floquet multipliers.

## Commands
- `run_sycl_worker_smoke.cmd`: build, device probe, persistent worker kernel smoke, FP32-vs-host-FP64 velocity parity.
- `run_archive_full_sycl.cmd`: FULL archive using external worker; on non-FP64 devices this is explicitly a screening campaign.
- `run_archive_full.cmd`: CPU/OpenMP FP64 confirmatory campaign.


## v0.4.5.3 lock-safe build publication

The worker filename is content-addressed by source, build flags, and compiler fingerprint. Compilation occurs into a unique temporary executable. This avoids overwriting a mapped `.exe` on Windows and prevents `LNK1104` after a preceding smoke or campaign.
