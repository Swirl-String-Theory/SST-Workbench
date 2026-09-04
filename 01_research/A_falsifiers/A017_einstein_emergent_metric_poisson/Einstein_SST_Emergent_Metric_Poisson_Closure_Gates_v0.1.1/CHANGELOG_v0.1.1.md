# v0.1.1 — MSVC / pybind11 shape-constructor compatibility fix

## Fixed

- Fixes MSVC C2665 in `cpp/einstein_sst_fast.cpp` when constructing multidimensional `py::array_t<double>` objects with mixed `py::ssize_t` and `int` dimensions.
- All NumPy array-shape dimensions are now explicitly cast to `py::ssize_t`, compatible with the stricter `pybind11::array::ShapeContainer` constructor resolution seen with Python 3.14 / current pybind11.
- Applies the same explicit typing to the resampling output shape to prevent the same class of failure there.

## Scope

No numerical equations, blind thresholds, gate definitions, or datasets were changed. This is a build-compatibility patch only.
