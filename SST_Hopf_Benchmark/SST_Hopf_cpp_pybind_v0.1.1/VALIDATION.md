# Validation — SST Hopf C++/pybind Benchmark Pack v0.1.1

## Status

| Check | Status | Notes |
|---|---|---|
| Python syntax compile | **PASS** | All eight step scripts, common module and runners compile under the audit Python environment. |
| Python reference QUICK chain | **PASS** | Steps 1–8 returned code 0. Summary in `validation/python_quick_run_summary.json`. |
| Python reference STANDARD chain | **PASS** | Steps 1–8 returned code 0. Summary in `validation/python_standard_run_summary.json`. |
| Native C++ source generated | **PASS** | `cpp/native.cpp` contains the accelerated numerical kernels and pybind11 module. |
| Native C++ compile in this sandbox | **NOT EXECUTED** | The sandbox does not provide the `pybind11` Python package/headers and its package mirror cannot supply them. This is an environment dependency limitation, not a recorded native PASS. |
| Native-vs-Python parity in this sandbox | **NOT EXECUTED** | Requires the compiled native module. `run_native_selfcheck.py` is included and is mandatory in `RUN_ALL.cmd`. |
| Windows one-click runner | **STATICALLY CHECKED** | `RUN_ALL.cmd` performs venv setup → strict native build → parity → standard H0–H10 run. |

## Validated Python-reference chains

### QUICK

```cmd
python run_all.py --tier quick --force-python --out-root results\validation_python_quick
```

Expected structural result: all eight processes return `0`. Scientific gates retain their epistemic status; open gates are not promoted to PASS merely because the process completed.

### STANDARD

```cmd
python run_all.py --tier standard --force-python --out-root results\validation_python_standard
```

Expected structural result: all eight processes return `0`.

## Required native validation on the target Windows workstation

Run:

```cmd
RUN_ALL.cmd
```

That command is intentionally strict. It must stop when native compilation or parity fails.

For the complete local validation ladder:

```cmd
RUN_FULL_VALIDATION.cmd
```

For the same ladder plus the high-resolution tier:

```cmd
RUN_FULL_VALIDATION_HIGHRES.cmd
```

## Release gate

The C++ backend should not be treated as validated until all of these are green on the target toolchain:

1. strict pybind11 build;
2. `run_native_selfcheck.py` parity;
3. quick C++ run;
4. standard C++ run;
5. C++/Python benchmark executes successfully;
6. optionally high-resolution run for final workstation evidence.

## Scientific-status guard

A process exit code of zero means the computation completed and its internal numerical criteria were satisfied where defined. It does **not** convert `DEMONSTRATION`, `SST_ANSATZ`, `CONDITIONAL_BRIDGE`, or `INDETERMINATE` gates into derived SST physics.

## v0.1.1 hotfix validation

The Windows build log was traced to mixed-type brace initializers passed to `py::array_t` shape constructors. The same pattern was removed from every multidimensional native allocation.

Independent validation in this environment:

- CPython 3.13 + GCC + OpenMP native compile: **PASS**.
- pybind11 3.0.1 headers: **PASS**.
- Native import / backend_info: **PASS**.
- C++ ↔ Python selfcheck: **14/14 PASS**.
- QUICK H0–H10 chain with native backend: **PASS**.
- STANDARD H0–H10 chain with native backend: **PASS**.
- `relative_l2` native semantics were also corrected to match the Python reference for numerator/reference arrays with different shapes (needed for the divergence residual).
- OpenMP `collapse(3)` loops were flattened to portable 1-D parallel loops, removing the MSVC C4849 warning path.
- Windows build order now prefers setuptools/MSVC before Strawberry/MinGW `c++`.

Target-machine gate still required:

- Python 3.14 + pybind11 3.1.0 + VS2022/MSVC: run `RUN_ALL.cmd`.

The package intentionally ships without a Linux `.so`; the local builder must create the correct Python 3.14 `.pyd` on Windows.
