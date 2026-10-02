# Validation v0.1.1

Software-portability hotfix validation. The scientific preregistration remains `configs/preregister_v0.1.0.json` unchanged.

Checks performed for this release:

- source audit confirms no unqualified/global `ssize_t` remains in `cpp/native.cpp`;
- NumPy array dimensions use `py::ssize_t`, which maps to Python/pybind11's platform-native signed size type;
- `native_ext.__init__` no longer imports `core` eagerly, preventing `native_ext.build_ext_if_needed` from being inserted into `sys.modules` before `runpy` executes it;
- Python fallback unit tests pass;
- synthetic control generation and campaign code remain unchanged from v0.1.0 except for the native build facade;
- blind salt, gates, thresholds, and normal/basic/extended configuration files are byte-identical to v0.1.0.

The actual MSVC build should be verified by `run_00_install.cmd` on Windows; this package was specifically patched for the compiler diagnostics reported from MSVC 14.44 / CPython 3.14.
