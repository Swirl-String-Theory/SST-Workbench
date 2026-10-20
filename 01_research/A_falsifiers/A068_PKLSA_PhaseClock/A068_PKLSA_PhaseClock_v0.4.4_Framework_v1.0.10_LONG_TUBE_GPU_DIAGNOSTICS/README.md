# A068 v0.4.4 — Framework v1.0.10 — Full Diagnostics + Intel Arc GPU

**Status:** DEVELOPMENT/UNFROZEN until official Windows FREEZE; framework v1.0.10 is **LOCAL_VALIDATED_CANDIDATE**. No physical Swirl Clock qualified.

## Install
Extract in a clean directory, run `SETUP_A068.cmd --workbench-root C:\\workspace\\projects\\SST-Workbench`. Verify A004 v0.2.2 first. The installer will refuse an existing v0.4.4 target and will not change v0.4.2 or older results. Then run `run_all.cmd BASIC`, `FULL`, and `CERTIFY` from the installed instance.

## Full diagnostics
All G0–G8 scientific evaluators attempt independent measurements via v1.0.10 `run_evaluators`. Framework recursive scientific qualification remains separate; G3/G4/G7/G8 will not claim physical PASS from geometric seeds. Manufactured Floquet is a software oracle.

## Actual Intel Arc GPU
Requires an appropriate Intel-XPU-capable PyTorch build and supported FFT/FP64 on the Arc A770; do not install CUDA-only torch or claim that the framework's SYCL/DD32 Biot-Savart smoke test proves whole-solver parity. The real GPU Euler FFT/RK4 parity screen writes `GPU_XPU_FULL_EULER_RK4_PARITY.json`, with `UNAVAILABLE_NO_FALLBACK` if the GPU route fails. Also run `run_all.cmd ALL` and `run_all.cmd DD32` from Framework v1.0.10 and inspect backend logs.

## Matrix
See `overlay/data/V044_REGISTERED_MATRIX.json`; large FULL/CERTIFY campaigns should run on the user's machine. All output files appear under the framework-controlled run-specific BLIND packaging. External A004 library is pinned; never replace its 40 XYZ datasets silently.
