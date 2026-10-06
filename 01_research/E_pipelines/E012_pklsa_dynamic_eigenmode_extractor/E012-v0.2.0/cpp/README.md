# Native backend ownership

E012-v0.2.0 intentionally contains no duplicate C++ kernel.

The native regularized Biot-Savart implementation remains owned by
`C006_kelvin_floquet_workbench/C006-v0.3.0`. E012 imports the C006 Python API,
which uses the existing C++17/pybind11 module when ABI-compatible and otherwise
falls back to the C006 Python reference implementation.

v0.2.0 additionally uses C006's RPO search API; it still does not fork the native
dynamics code. This keeps one authoritative scientific kernel.
