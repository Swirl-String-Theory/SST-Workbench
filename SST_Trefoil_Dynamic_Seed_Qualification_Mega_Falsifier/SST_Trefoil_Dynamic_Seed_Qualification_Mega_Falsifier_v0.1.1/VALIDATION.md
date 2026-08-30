# Validation — v0.1.1

## v0.1.1 regression target

The Windows BASIC log reached the native selftest (`native_python_rel_l2 = 0.0`) and `4 passed`, then failed in S50 because S40 JSON-cleaning converted non-finite recurrence sentinels to `null`. v0.1.1 treats those rows as ineligible and continues fail-closed. It also prevents S40 mesh-gate failures from entering S50.


v0.1.1 patch-environment checks:

- Python syntax compilation: **PASS**.
- Pytest regression suite: **8/8 PASS** (original 4 tests + 4 S40→S50 boundary tests).
- Explicit null-return CLI smoke: **PASS**; S50 emits `FAIL_NO_PROJECTED_STABLE_RPO` with rejection reason `NO_FINITE_BEST_RETURN` and no traceback.
- S40 mesh-gate inheritance regression: **PASS**.
- `cpp/native.cpp` SHA-256 remains `03b3b985532abe8d2d1a218620793a0b17a2d77e195e4b1f71c9198646d37c18`, byte-identical to v0.1.0.
- The supplied Windows v0.1.0 run compiled that unchanged C++ source successfully and reported `backend = cpp-pybind11-openmp`, `native_python_rel_l2 = 0.0`, self-alignment `1.8344567888170168e-16`, and **4/4 tests PASS** before the S50 Python boundary failure.
- The v0.1.1 patch environment itself did not recompile the native module because its system Python lacks the `pybind11` package; no C++ code changed in this release. The normal Windows `run_01_build_native.cmd` remains part of every full/resume chain.

The earlier v0.1.0 generation-environment end-to-end synthetic smoke remains relevant to unchanged S10-S40/S50 numerical machinery, but is **workflow validation only, not physics evidence**.
