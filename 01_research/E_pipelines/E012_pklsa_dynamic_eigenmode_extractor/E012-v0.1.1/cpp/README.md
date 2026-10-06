# Native backend ownership

E012-v0.1.0 intentionally contains no duplicate C++ kernel.

The native regularized Biot–Savart implementation remains owned by
`C006_kelvin_floquet_workbench/C006-v0.3.0`.  E012 imports the C006 Python API,
which uses the existing C++17/pybind11 module when available and otherwise falls
back to the C006 Python reference implementation.

This avoids two independently drifting copies of the same scientific kernel.
