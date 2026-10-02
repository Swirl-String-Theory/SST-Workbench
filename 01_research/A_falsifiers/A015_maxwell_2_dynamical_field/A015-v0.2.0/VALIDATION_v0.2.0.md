# Validation — 2_Maxwell_SST_Dynamical_Field_Closure_Falsifier_v0.2.0

Validation date: 2026-08-13.

## Source lineage

- v0.1.0 blind DFC-T / DFC-D / DFC-G falsifier retained.
- Native build/load/fallback architecture adapted from the supplied `SST_cpp_pybind_audit_template(1).zip`.
- Relaxed-knot intake validated against the supplied `KnotPlot_relaxed_final.zip`, corresponding to the user's Windows directory `C:\workspace\projects\SST-Workbench\KnotPlot\knots\final`.

## Functional validation

1. Synthetic positive control: DFC-T PASS, DFC-D PASS, DFC-G PASS.
2. Three gate-specific negative controls: each fails its intended gate.
3. Pytest geometry/native-independent tests: 2 passed.
4. Native C++ / Python parity on a resampled trefoil:
   - interaction-energy relative error: `2.26e-15`;
   - interaction-force relative error: `2.90e-16`.
5. BASIC relaxed-knot campaign:
   - `knot_3.1_final.txt`, `knot_4.1_final.txt`, `torus_2.3_final.txt`;
   - geometry audit: 3/3 PASS;
   - native parity: PASS.
6. EXTENDED campaign over the supplied final directory:
   - 41 `*_final.txt` geometries;
   - knots and 2-/3-component links accepted;
   - geometry audit: 41/41 PASS;
   - native parity: PASS;
   - x/y/z reduced pair scans completed;
   - median analytic-gradient / local finite-difference NRMSE approximately `1.92e-10`;
   - maximum group NRMSE approximately `2.65e-8`.

## Environment caveat

The native C++ source and setuptools build path were compiled and executed in the available Linux/Python 3.13 validation environment. The Windows `.cmd` wrappers and MSVC build path cannot be executed inside this environment. They are written for the user's Windows layout and the install script explicitly requires a working Visual Studio C++ build toolchain if no compatible compiler is already available.

## Scientific guard

The reduced centerline interaction scan is `SURROGATE_ONLY`. It is a fast geometry/kernel diagnostic, not canonical DFC-G evidence. It does not satisfy the `force_independent=true` requirement of the blind gravity gate. Static centerlines also do not contain the unreduced time-dependent data required for DFC-T or the independent polarization/current/charge channels required for DFC-D.
