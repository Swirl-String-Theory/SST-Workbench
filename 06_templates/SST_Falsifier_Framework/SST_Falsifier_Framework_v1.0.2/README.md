# SST Falsifier Framework v1.0.2

Canonical shared runtime for SST-Workbench falsification projects. It consolidates the useful infrastructure from the former blind multi-library, C++/pybind11 and GPU/SYCL templates while keeping numerical backends independent.

## Canonical Workbench location

```text
SST-Workbench/
└── 06_templates/
    └── SST_Falsifier_Framework/
        ├── SST_Falsifier_Framework_v1.0.0/
        ├── SST_Falsifier_Framework_v1.0.1/
        └── SST_Falsifier_Framework_v1.0.2/
```

No framework/template discovery path under `04_tools/D_proof` is used by v1.0.2. Generated falsifiers store a relative `.sst_framework_root` locator and can also discover the newest version under the canonical nested `06_templates/SST_Falsifier_Framework/` family.

Scientific instances remain under `01_research/A_falsifiers/...`.

## Core rule

A `PASS` is valid only when the preregistered source, implementation and precision class actually ran. Silent backend fallback cannot satisfy a certification gate.

## Profiles

- `minimal`: Python FP64/reference only.
- `cpu`: Python FP64 reference + strict C++/pybind11 FP64 certification.
- `gpu`: Python FP64 + C++ FP64 + SYCL FP32 screening + DD32/FP32x2 high-precision screening.
- `multilibrary_gpu`: same backend ladder plus independent multi-source discovery/confirmation contract.

## v1.0.2 precision lanes

The backend selftest runs the same regularized midpoint Biot--Savart kernel through:

```text
Python/NumPy FP64           REFERENCE
C++/pybind11 FP64          CERTIFICATION
SYCL FP32                   SCREENING_ONLY
SYCL DD32 / FP32x2         SCREENING_ONLY (high-precision candidate)
```

DD32 is double-single arithmetic:

\[
x \approx x_{\rm hi}+x_{\rm lo},\qquad x_{\rm hi},x_{\rm lo}\in\mathrm{binary32}.
\]

It is **not IEEE FP64** and not an IEEE-defined `FP48` format. Its exponent range remains binary32; the nominal significand capacity is roughly 48 bits. Actual accuracy is measured against the FP64 reference on every selftest. See `docs/DD32_FP32X2.md`.

Default DD32 gates:

```text
velocity relative-L2              <= 1e-8
directional finite-diff rel-L2    <= 2e-6
improvement over ordinary FP32    >= 20x
```

The SYCL worker is compiled with `-fp-model=precise` so reassociation/fast-math cannot silently invalidate TwoSum/FMA residual arithmetic.

## C++ compiler provenance fix

v1.0.2 no longer reports the first `c++.exe` found on `PATH` as the pybind compiler. It records the compiler executable actually emitted by the setuptools build command, including compiler family, version, MSVC toolset when available, Python ABI and compile flags. This prevents a Strawberry/MinGW `c++.exe` from being recorded when the extension was actually built by Visual Studio `cl.exe`.

## Local test

From the framework root:

```bat
run_all.cmd ALL
```

This performs:

1. environment setup;
2. framework/unit integrity tests;
3. full backend parity including DD32.

Run only the backend parity:

```bat
run_all.cmd BACKENDS
```

Run only the Arc FP32/DD32 precision smoke:

```bat
run_all.cmd DD32
```

Results:

```text
build/BACKEND_SELFTEST.json
build/DD32_PARITY_SMOKE.json
```

## Create a falsifier

```bat
python tools\new_falsifier.py A056 my_falsifier ^
  C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A056_my_falsifier\A056-v0.1.0 ^
  --profile multilibrary_gpu --version v0.1.0
```

Then complete `science_contract.json`, source/gate/blind contracts, the experiment pipeline, and `report/FALSIFIER_REPORT.tex` before freezing.

## Instance run modes

```text
run_all.cmd SELFTEST
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
run_all.cmd REVEAL
```

## Output policy

For `<Name>_vX.Y.Z`:

```text
./<Name>_vX.Y.Z-outputs/
../<Name>_vX.Y.Z-outputs_BLIND.zip
../<Name>_vX.Y.Z-outputs_REVEALED.zip
```

The output report directory contains the frozen human-readable LaTeX protocol plus generated science/results fragments and provenance.

## Scientific report contract

Every generated falsifier contains `report/FALSIFIER_REPORT.tex`. It is part of the preregistration bundle and must explain the research question, hypotheses, assumptions, equations, dimensional checks, numerical implementation, source independence, gate DAG, convergence/error budget, backend authority, blindness/reveal rules and post-run interpretation limits.

The v1.0.2 template also documents DD32 explicitly so it cannot be mislabeled as FP64.

## Release cleanliness

Source packages reject generated `.pyd`, `.dll`, `.exe`, `.lib`, `.exp`, `.obj`, `.pyc`, `__pycache__`, `.pytest_cache`, `.venv`, `build/` and prior output trees.
