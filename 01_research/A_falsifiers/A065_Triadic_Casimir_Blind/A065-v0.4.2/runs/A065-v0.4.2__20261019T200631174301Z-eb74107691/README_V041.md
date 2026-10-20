# A065-v0.4.1 — Arc A770 volumetric Euler backend (GPU screening)

## Previously available, reused

- **SST Falsifier Framework v1.0.10 CANONICAL_FROZEN** remains external and untouched.
- Existing SYCL DD32/Biot-Savart worker is a separate **kernel-only** certification,
  NOT a 3D FFT/RK4 validation and NOT automatically reused as an Euler operator.
- A003 Fourier Knot Import Adapter v0.2.3 and original 384-record atlas v0.1.2.
- A065-v0.4.0 baseline with 48^3, 64^3, 96^3, Gaussian a=0.55, L=12,
  Gamma=1, rho=1, Euler T=0.02, RK4 steps=4. No changes to this contract.

## New actual GPU solver

`triadic/gpu_euler_v041.py`: dpnp SYCL device-memory FFTs, Fourier projection,
  nonlinear rotational Euler RHS, RK4, curl, Poisson pressure. The GPU selection
  explicitly requires **Intel Arc A770 Level Zero**; Intel UHD, SYCL CPU and
  missing dpnp all produce NOT_RUN_PREREQUISITE. No fallback disguised as GPU.
  GPU arithmetic is native **FP32**; the existing DD32 worker does NOT certify
  DD32 FFTs. The independent control is host NumPy FFT **FP64**.

## Run locally on Windows

Set your existing three paths (Framework, A003 adapter, A003 atlas). Activate
A065's existing `.venv` and install optional Intel GPU Python dependencies in
that environment (do not touch the frozen framework):

```bat
.venv\Scripts\python.exe -m pip install -r requirements_arc_v041.txt
run_all.cmd VERIFY
run_all.cmd SELFTEST
run_all.cmd GPU_SMOKE
run_all.cmd GPU_CAMPAIGN
run_all.cmd ALL
```

`GPU_SMOKE`: real A770 Taylor-Green 24^3 Euler time integration vs NumPy FP64,
 including numerical pressure. `GPU_CAMPAIGN`: real A003 direct/Hoste geometries,
 three grids each, each integrated GPU FP32 and CPU FP64 for parity. It can
 take time and multiple GB temporary memory; run while plugged into AC power.
 No FP32 physics-certification at near-threshold sensitivity.

Optional `set A065_V041_SAVE_FIELDS=1` saves six GPU NPZ snapshots (u, omega, p,
 source geometry hash, kernel label). No independent pressure measurement.

## New official framework gates

- G43: Arc Level Zero device present and used; no silent CPU/iGPU fallback.
- G44: Taylor-Green GPU-vs-CPU numerical parity.
- G45: authenticated A003 48/64/96 Euler velocity + vorticity parity.
- G46: dependent numerical pressure parity.
- G47: fully realized GPU ladder with source provenance, not physical claims.
- G48: PKLSA physical source-native and independent holdout remain UNRESOLVED.

The official FULL run computes these gates independently from negative G2,G24,
G29,G31,G35. In a container without Arc the GPU gates are NOT_RUN_PREREQUISITE,
never PASS. Unexpected GPU operator failures remain exceptions (fail-closed).

## Caution

The phrase *3D Euler solution* means a **numerically integrated PDE IVP** from
an *assumed Gaussian vortex tube*, not derived native PKLSA material response,
independent physical pressure observation, Casimir closure, or gravity theory.
