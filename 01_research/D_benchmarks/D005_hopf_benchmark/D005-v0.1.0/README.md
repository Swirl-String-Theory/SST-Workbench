# SST Hopf C++/pybind Benchmark Pack v0.1.0

C++17/pybind11 acceleration of the eight SST Hopf H0–H10 research scripts.

This package follows the established `SST_cpp_pybind_audit_template` pattern:

- hash-based native rebuild when `cpp/native.cpp` changes;
- pybind11 `_native` extension inside a Python package;
- transparent Python/NumPy fallback;
- C++/Python parity self-check;
- one-command audit runners;
- JSON/NPZ evidence retained from the original eight scripts.

## One-click Windows run

From `cmd.exe`:

```cmd
RUN_ALL.cmd
```

That performs, in order:

1. creates `.venv` when needed and installs `numpy` + `pybind11`;
2. compiles the C++17 extension;
3. runs native-vs-Python parity checks;
4. runs all eight steps in the **standard C++ tier**;
5. writes `results\standard_cpp\run_summary.json` plus per-step logs/evidence.

Other top-level runners:

```cmd
RUN_QUICK.cmd
RUN_HIGHRES.cmd
RUN_FULL_VALIDATION.cmd
RUN_FULL_VALIDATION_HIGHRES.cmd
```

`RUN_FULL_VALIDATION.cmd` is the recommended complete workstation check: strict native build → C++/Python parity → quick C++ chain → standard C++ chain → timing benchmark. `RUN_FULL_VALIDATION_HIGHRES.cmd` adds the high-resolution chain after those gates pass.

`RUN_HIGHRES.cmd` reaches 3-D grids up to `N=128` and can require several GB of RAM because the Hopf field, curvature, Fourier arrays and temporary NumPy buffers coexist.

## Eight research steps

| Script | Gates | Purpose |
|---|---|---|
| `01_definieer_sst_orderparameter.py` | H4 | SST order-parameter candidate |
| `02_analytische_hopf_benchmark.py` | H0–H3 | exact Hopf benchmark, gauge and linking |
| `03_toroflux_spinorveld.py` | H4 | toroflux spinor/director ansatz |
| `04_hopf_lading_numeriek.py` | H1–H3 | spinor/director/preimage routes |
| `05_heliciteitsbridge.py` | H5 | `H = Gamma^2 Q_H` bridge test |
| `06_effectieve_spinactie.py` | H6–H8 | Berry coefficient / conditional quantization |
| `07_vier_pi_configuratieruimte.py` | H9 | SU(2) 2pi/4pi diagnostic |
| `08_trefoil_integratie.py` | H10 | trefoil + Hopf evidence integration |

The matching design documents are under `docs/steps/`.

## What is accelerated in C++

`cpp/native.cpp` contains C++17 kernels for:

- spinor normalization;
- Hopf map;
- spinor/director norm residuals;
- analytic Hopf spinor evaluation;
- 3-D finite-difference spinor connection;
- curl and divergence;
- director curvature `b`;
- Hopf-charge integration;
- relative L2 residuals;
- Gauss linking integral;
- torus-knot centerline generation;
- Bishop frame construction;
- polygonal writhe;
- material-frame twist;
- SU(2) rotation matrices;
- structured tube spinor/director generation.

The Coulomb-gauge reconstruction in step 4 deliberately stays in NumPy FFT:

```text
A_k = i k x B_k / |k|^2
```

because the minimal template does not introduce a second native FFT dependency. Thus this is a **hybrid C++/NumPy fast path**, not a claim that every operation runs in C++.

## Backend selection

Default behavior is native C++ when the extension is available.

Force the Python reference implementation:

```cmd
set SST_HOPF_FORCE_PYTHON=1
python run_all.py --tier standard --force-python
```

Force native rebuild:

```cmd
python -m sst_hopf_native.build_ext_if_needed --force --strict
```

Show backend information:

```cmd
python -c "from sst_hopf_native import backend_info; print(backend_info())"
```

With OpenMP support the backend reports the available thread count. The builder first attempts an OpenMP build and automatically retries without OpenMP if the compiler/toolchain does not support it.

## CMD runner map

```text
RUN_ALL.cmd
RUN_QUICK.cmd
RUN_HIGHRES.cmd

cmd/
  00_SETUP_VENV.cmd
  01_BUILD_CPP.cmd
  02_RUN_QUICK_CPP.cmd
  03_RUN_STANDARD_CPP.cmd
  04_RUN_HIGHRES_CPP.cmd
  05_RUN_NATIVE_PARITY.cmd
  06_BENCHMARK_CPP_VS_PYTHON.cmd
  07_RUN_STANDARD_PYTHON_REFERENCE.cmd
  08_CLEAN_BUILD.cmd
  steps/
    01_H4_ORDER_PARAMETER.cmd
    02_H0_H3_HOPF_BENCHMARK.cmd
    03_H4_TOROFLUX.cmd
    04_H1_H3_HOPF_CHARGE.cmd
    05_H5_HELICITY.cmd
    06_H6_H8_SPIN_ACTION.cmd
    07_H9_FOUR_PI.cmd
    08_H10_TREFOIL.cmd
```

The individual step runners are useful for iterating after a full run. Steps 4 and 5 automatically run their prerequisite manual step when its NPZ is absent.

## Python runner tiers

```cmd
python run_all.py --tier quick
python run_all.py --tier standard
python run_all.py --tier high
```

### Quick

- low-resolution exploratory work;
- H0–H10 pipeline check;
- Hopf benchmark still reaches `N=64` because step 4 is not meaningful enough at `N=32` with the current finite-difference/director reconstruction.

### Standard

- step 2: `N = 24, 32, 48, 64`;
- default recommended routine run.

### High

- step 2: `N = 48, 64, 96, 128`;
- larger toroflux and trefoil samples;
- intended for final local workstation checks.

## Native parity test

```cmd
cmd\05_RUN_NATIVE_PARITY.cmd
```

`run_native_selfcheck.py` compares the C++ implementation with the untouched Python reference functions for normalization, Hopf map, derivatives, curvature, charge, centerline, Bishop frame, writhe, twist and Gauss linking.

A release should not be trusted if this parity test is red.

## Performance benchmark

```cmd
cmd\06_BENCHMARK_CPP_VS_PYTHON.cmd
```

or:

```cmd
python benchmark_cpp_vs_python.py 64
```

The result is written to:

```text
results/cpp_vs_python_benchmark.json
```

## Compiler requirements on Windows

Recommended:

- Python 3.10+;
- NumPy;
- pybind11;
- Visual Studio 2022 Build Tools with **Desktop development with C++**.

The builder retains the template strategy: direct compiler attempt first, then a setuptools/MSVC fallback. The package remains runnable in Python mode when C++ compilation is unavailable, but `RUN_ALL.cmd` intentionally uses `--strict` for the native build because its purpose is to verify the C++ route.

## Epistemic guard

C++ acceleration does not change the scientific status of a gate. In particular:

- H5 without independent SST velocity/vorticity remains `DEMONSTRATION`;
- H6 with a synthetic trajectory remains `DEMONSTRATION`;
- H7/H8 remain `INDETERMINATE` without the required physical evidence;
- H9 remains `INDETERMINATE` without a configuration-space/Finkelstein–Rubinstein certificate;
- H10 remains `INDETERMINATE` until the required upstream gates and external knot/event evidence close.

The native backend accelerates the calculation; it does not promote an ansatz into a derivation.
