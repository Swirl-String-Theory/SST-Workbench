# Framework integration

A054-v0.4.0-r1 is a thin scientific instance of **SST Falsifier Framework v1.0.4 CANONICAL_FROZEN**.

- canonical path: `06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.4`
- expected supplied ZIP SHA-256: `1bdf8a20f0f0cbdf86ab89fb198d1930e0694579dee8d5dcd35149972c0d2104`
- expected framework `PACKAGE_MANIFEST.json` SHA-256: `1a9e98ee7762ab12746e5327a6552348d5e2edbee8ddaebc557ebaeb261e7452`

The instance does not vendor or patch the framework. `run_instance.py` fails closed if another framework tree is resolved. Python/NumPy FP64 is reference arithmetic; C++17/OpenMP FP64 is certification; SYCL FP32/DD32 remains optional screening only.
