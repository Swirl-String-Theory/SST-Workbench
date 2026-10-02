# Template provenance

v0.3.0 is an extension of `SST_Threaded_Hole_Substrate_Blind_Falsifier_v0.2.1` and follows the user's `SST_cpp_pybind_audit_template` architecture:

- Python reference implementation;
- C++17/pybind11 hot kernels;
- OpenMP acceleration when available;
- Windows `.cmd` install/build/run entry points;
- blind prepare -> blind compute -> SHA-256 seal -> reveal workflow;
- pytest validation.

The new Kelvin/M'Farlane tracer computations call the existing C++ `field_velocity` kernel at every integration stage, so the expensive Biot--Savart sampling remains in native code when the extension is built.
