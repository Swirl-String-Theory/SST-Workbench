# Windows SYCL diagnostics (v0.4.3)

Run `run_sycl_diagnostics.cmd` before a FULL SYCL campaign.

Stages:
1. pybind module compiled with `-fsycl`, no SYCL symbols.
2. SYCL GPU device enumeration, no device kernel.
3. Named FP32 device kernel.
4. FP64 capability probe. The Arc A770 is expected to report native `aspect::fp64 == false`; the FULL scientific solver remains double precision and must not silently downcast.

The normal SYCL extension uses a named kernel, per-kernel device-code splitting, isolated import validation, and `SYCL_CACHE_PERSISTENT=0` in launcher scripts.
