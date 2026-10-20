# SST GPE XPU numerical falsifier installer v0.1.0

**Requires exact SST_Falsifier_Framework_v1.0.10 from SST-Workbench. This version is LOCAL_VALIDATED_CANDIDATE, NOT CANONICAL_FROZEN; this installer does not modify it.**

## Windows quickstart

1. Unzip this package anywhere on your Windows machine.
2. Ensure framework exists at `C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10`.
3. Double-click `run_all.cmd` or execute `run_all.cmd BASIC`. The bootstrap generates an immutable-contract-ready instance in `01_research\F_exploratory\GPE_EXT_001_GPE_GPU_Benchmark_v0.1.0`, creates a `.venv`, installs XPU PyTorch (may be a large download), retrieves Zenodo source with checksum verification, freezes the pre-registered scientific protocol (on first run), and runs BASIC.
4. For heavier benchmarks: `run_all.cmd FULL`; use `run_all.cmd DATA` to fetch only. Outputs and PDF/ZIP are produced by the shared framework, outside the instance root per its policies; report PDF requires TeX Live/MiKTeX.
5. Optional `SST_WORKBENCH_ROOT=...` overrides the canonical Workbench root. The installer never rewrites an existing framework or previously installed instance with an unknown stamp.

## Benchmarks and genuine limitations

- NumPy FP64 TSSP periodic GPE plane-wave analytic check, norm and reverse-time check, fixed-final-time second-order convergence.
- PyTorch Intel XPU `torch.fft.fftn` and `torch.fft.ifftn` GPE operator execution, FP32 comparison against independent NumPy reference. **No CPU fallback disguised as GPU**.
- External dataset: Zenodo 20068724, `Vortex-shedding-PRR-data-1.0.0.zip`, MD5 `59256e30ecd9e956d911c32f7a16d55b`, ZIP CRC and SHA-256 local manifest. Published **processed diagnostics only**; external full-field comparison **not implemented**, so G4/G7/G8 physical claims remain unavailable.
- G0/G1/G2/G3/G6 scientific gate callbacks integrated through v1.0.10 `ledger.run_evaluators`. No G3/G6 PASS can certify Euler/PKLSA dynamics, gravity, Casimir or Swirl Clock.
- Disables native C++ G5 because this bundle has **no separate native GPE solver**. `torch.xpu` is not advertised as the framework's SYCL native backend.
- GPU output type is complex64 (screening only) and no arbitrary GPE-physical units or material parameters are implied.
- Real GPU execution and framework outputs require the user's Windows Intel Arc A770; cannot be hardware-validated on a CPU-only build host.
- Pin the installed torch version in the *output environment manifest*; this development tool does not claim identical wheels will be served indefinitely. For fully immutable rebuilds add a wheel lock SHA file after the first validated build.

## Gate status policy

`G0`: framework verified freeze; `G1`: published source integrity; `G2`: exact reference; `G3`: temporal order; `G6`: actual XPU CPU↔GPU parity. `G4,G5,G7`: disabled on scientific grounds. `G8`: UNRESOLVED, physics-provider absent. `G9`: DEFERRED separate reveal. Hardware not available: `G6` NOT_RUN_PREREQUISITE, not PASS.

## Citations

- Gross (1961), Nuovo Cimento, 20:454–477, https://doi.org/10.1007/BF02731494
- Pitaevskii (1961), Sov. Phys. JETP, 13:451, http://www.jetp.ras.ru/cgi-bin/dn/e_013_02_0451.pdf
- Bao, Jaksch and Markowich (2003), J. Comput. Phys., 187:318–342, https://doi.org/10.1016/S0021-9991(03)00102-5
- Kwon and Shin (2026), Zenodo processed datasets, https://doi.org/10.5281/zenodo.20068724
- ETH Zurich, TorchGPE implementation background: https://github.com/qo-eth/TorchGPE
- PyTorch Intel XPU setup: https://pytorch.org/get-started/additional-platforms/
