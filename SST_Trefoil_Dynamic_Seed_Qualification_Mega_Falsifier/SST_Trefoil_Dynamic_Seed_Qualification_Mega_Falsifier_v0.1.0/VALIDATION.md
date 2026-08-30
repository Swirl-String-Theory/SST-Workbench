# Validation — v0.1.0

Generation-environment checks:

- Python syntax compilation: **PASS**.
- Pytest: **4/4 PASS**.
- Explicit MSVC audit: native source uses `py::ssize_t`; no global `ssize_t`: **PASS**.
- Native C++17/OpenMP source compiled and imported in the generation environment using locally available pybind11 headers: **PASS**.
- Native/Python velocity relative L2 error on a 64-point analytic trefoil: `2.898329577875693e-17`: **PASS**.
- Self-alignment residual: `5.650530578218433e-17`.
- End-to-end tiny synthetic campaign executed through S10 prepare → S20 rolling → S25 blind local refinement → S30 resolution → S35 core-radius robustness → S40 long recurrence → S50 projected Floquet → S60 finite-core causal gate → S70 reveal: **PASS as a workflow smoke test**.
- The smoke config used deliberately permissive thresholds and is **not physics evidence**.

The normal Windows path is `run_00_setup.cmd` followed by `run_01_build_native.cmd`; it uses the installed `pybind11` Python package and MSVC C++17/OpenMP.
