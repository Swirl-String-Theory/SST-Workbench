# Package validation

Validation performed in the build environment before packaging:

- Python syntax compilation: PASS.
- Multi-component XYZ parser: PASS.
- Uniform closed-curve resampling: PASS.
- Periodic normal/binormal frame construction: PASS.
- Rigid translation+rotation least-squares recovery: PASS.
- C++17/OpenMP `native.cpp` compilation: PASS (manual local compile using available pybind11 headers).
- Native-vs-NumPy regularized Biot–Savart circle test: relative L2 error `2.94e-16`.
- Native one-case blind campaign smoke test: PASS (pipeline completion, report generation, no exception).
- Full **basic** campaign over its 8 fixed real relaxed datasets using the Python reference backend: pipeline PASS, no numerical exceptions.
- Full **extended** campaign over all 41 supplied `*_final.txt` datasets using the Python reference backend: pipeline PASS, no numerical exceptions.

The validation above certifies software execution and native/reference agreement. It does **not** pre-certify any physical Kelvin/SST gate as PASS.
