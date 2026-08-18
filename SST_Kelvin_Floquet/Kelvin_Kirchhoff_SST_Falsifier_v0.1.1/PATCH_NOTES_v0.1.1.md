# Kelvin–Kirchhoff SST Falsifier v0.1.1 — Windows/MSVC hotfix

## Fixed

`cpp/native.cpp` used the POSIX type name `ssize_t` directly. GCC/Clang commonly expose
that symbol transitively, but Microsoft Visual C++ does not. Under VS2022 / Python 3.14 this
caused the first hard error:

```text
cpp/native.cpp(23): error C2061: syntax error: identifier 'ssize_t'
```

All subsequent `offsets`, `nt`, `nc`, OpenMP-loop, and function-header errors were parser
cascade errors from that first missing type.

The native binding now uses pybind11's portable index type explicitly:

```cpp
py::ssize_t
```

and uses `std::size_t` for the segment-vector reserve conversion.

## Scope

No numerical formula, regularization kernel, blind preregistration gate, threshold, dataset
selection, or scoring rule was changed. This is a compiler-portability hotfix only.

## Intended Windows target

- Visual Studio 2022 MSVC
- Python 3.14 x64
- pybind11 3.x
- NumPy 2.x
- OpenMP enabled when available, with the existing non-OpenMP retry preserved

Run:

```cmd
run_all.cmd 16
```
