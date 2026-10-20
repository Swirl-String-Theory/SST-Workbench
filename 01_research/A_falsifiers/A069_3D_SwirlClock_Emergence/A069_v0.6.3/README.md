# A069 v0.6.3 — Intel Arc A770 GPU **preflight**, DEVELOPMENT

**Not a frozen falsifier release. Not GPU-certified.** This package validates whether a local Windows Arc A770 can execute the complex 3D FFTs and normalized 3D GP Strang integrator from A069 v0.6.2 in `complex64`, and compares its results with an independent NumPy `complex128` reference. It does **not** generate a trefoil eigenfrequency or replace the canonical v0.6.2 campaign.

## Findings from source review

- Framework **v1.0.10** in Google Drive is `LOCAL_VALIDATED_CANDIDATE`, not yet `CANONICAL_FROZEN`. Its new ability is non-short-circuit evaluation and recursive scientific qualification. C++/SYCL/DD32 kernel implementation is inherited unchanged from v1.0.9; those kernels are **Biot–Savart/reference backend**, not the A069 3D GP FFT solver. Windows hardware parity is pending.
- User's `vec_add.cpp` is a **strict** SYCL GPU compute test. `main_sycl.cpp` enumerates devices but falls back to `default_selector_v` (which can silently select a CPU). `list_sycl_devices.cpp` is device enumeration only. None carries out GP complex FFTs.
- `xpu_audio.zip` includes a useful PyTorch XPU device/hardware check. Its `xpu.py` and scripts are for XTTS speech synthesis, and the older `intel_extension_for_pytorch` dependency is version-sensitive. No GP 3D FFT, time-step or precision parity test is included.
- `fs_production_run_seeddiag_toposafe_v4_folder_fseries_patched(1).py` uses PyTorch tensor fields with `get_device()` from a **missing** `fs_relax_xpu` module; it tests a Hopf-charge/relaxation hypothesis and is **not** a GP solver. It must not be treated as evidence for trefoil Swirl Clock stability. Its optional `knotplot`/`.fseries` source discovery is intentionally **not reused** in A069.

## Windows preflight, on your Arc A770 machine

Use a **separate** Python 3.11/3.12 environment if you do not already have a working Intel-XPU installation. Do **not** replace the canonical framework venv. Install `numpy`, `pytest`, and Intel-XPU PyTorch following the current [PyTorch Intel XPU installation guide](https://pytorch.org/get-started/additional-platforms/). Example when using a Python supported by the chosen PyTorch wheel:

```bat
py -3.12 -m venv .venv-xpu
.venv-xpu\Scripts\python.exe -m pip install --upgrade pip
.venv-xpu\Scripts\python.exe -m pip install numpy pytest
.venv-xpu\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/xpu
.venv-xpu\Scripts\python.exe -m pytest -q tests
.venv-xpu\Scripts\python.exe gp_xpu_probe.py --device xpu --expected-name A770 --n 32 --steps 8 --out results\A770_N32.json
.venv-xpu\Scripts\python.exe gp_xpu_probe.py --device xpu --expected-name A770 --n 64 --steps 8 --out results\A770_N64.json
```

The script **fails closed** without the expected A770, without supported complex 3D FFTs, or if its conservative estimated VRAM exceeds current available VRAM. All GP steps remain on `xpu` until the final comparison; output records exact detected GPU, torch build, FFT errors, CPU parity, timings and VRAM metrics. A CPU result is never labeled a GPU PASS.

The CPU-only smoke is available even without Intel GPU:

```bat
python -m pytest -q tests
python gp_xpu_probe.py --device cpu --n 32 --steps 8 --out results\CPU_N32.json
```

## Next: use a real B160 checkpoint from **v0.6.2**, after XPU32/64 pass

```bat
.venv-xpu\Scripts\python.exe gp_xpu_probe.py --device xpu --expected-name A770 --checkpoint "C:\PATH\TO\B160\T000016.npz" --allow-large --steps 4 --out results\B160_FROM_CHECKPOINT.json
```

The script reads the exact GP model coefficients (`mu`, `dt`, `box`, `xi`), 3D complex state, source marker and step index from your **existing** checkpoint. It creates its *own* JSON output, does not overwrite the original and computes a CPU-FP64 comparison unless `--no-cpu-reference` is explicitly requested. A large run without that independent comparison remains `UNRESOLVED` for parity. Run IDs, per-file hashes and official framework integration still need to be implemented in a versioned GP backend instance before production.

Do not try A512 as a first XPU run: `complex64` array=1 GiB on 512^3, but FFT workspaces and temporary fields can overflow 16 GiB. The intentionally conservative development VRAM guard rejects such a run until a measured memory-optimized implementation exists. B160 -> B192 -> B256 is the sensible progression.

## Qualification

The supplied development default is `2e-4` **screening** relative-L2 for CPU-FP64 versus GPU-FP32/complex64; it is **not** the framework DD32 certification threshold and **not** a physically justified A069 topological or clock acceptance tolerance. Pre-register stricter tolerances from time/grid convergence before allowing GPU results to influence G34, G35 or the A061 transfer.

Current scientific claims remain: `G32` depends on chosen geometry, `G34=UNRESOLVED`, `G35=UNRESOLVED`. No XPU results could be produced in the development environment because only a CPU torch installation is available.
