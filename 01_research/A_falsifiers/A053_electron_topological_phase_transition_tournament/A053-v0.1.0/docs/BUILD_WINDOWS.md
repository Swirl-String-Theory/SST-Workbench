# Windows native build

`run_build_cpp.cmd` creates/uses the local `.venv`, installs `pybind11`, `cmake` and `ninja`, asks the active Python installation for the exact `pybind11` CMake package directory, configures the native extension, builds it, and stages compiler runtime dependencies.

## MinGW / Strawberry Python-extension loading

When CMake selects a GNU/MinGW compiler such as Strawberry's `c++.exe`, a successful `.pyd` build can still fail at import time with:

```text
ImportError: DLL load failed while importing a053_native:
The specified module could not be found.
```

This usually means the `.pyd` was found but one of its runtime dependencies was not. A053 v0.1.0 buildfix2 handles this in three ways:

1. MinGW builds request static linkage of `libgcc` and `libstdc++` where supported.
2. `tools/stage_native_runtime.py` resolves common MinGW runtime DLLs with the configured compiler and copies any required DLLs beside the `.pyd`.
3. `tools/native_parity.py` explicitly registers both `build/` and the compiler runtime directory with `os.add_dll_directory()` before importing the extension.

The staging script also uses the toolchain's `objdump` when available to print the PE import table, making any remaining missing DLL explicit.

## Commands

```cmd
run_build_cpp.cmd
run_native_parity.cmd
```

If the GNU/MinGW extension still cannot load after the staged-runtime diagnostics, use an **x64 Visual Studio 2022 Developer Command Prompt**, delete `build`, and rerun `run_build_cpp.cmd`. This allows CMake to select MSVC, which is the native toolchain used by standard Windows CPython distributions.
