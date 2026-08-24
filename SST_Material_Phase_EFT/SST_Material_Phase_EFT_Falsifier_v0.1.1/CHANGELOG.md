# Changelog

## v0.1.1 — MSVC/native repair + verdict hardening

### 1. Windows/MSVC C++ build fixed

**Observed v0.1.0 failure:** `native_ext/_native.cpp` used POSIX `ssize_t`. MSVC 14.44 does not define that type by default, so parsing failed before the OpenMP loop and the extended campaign never started.

**Change:** all native array/loop indices now use Python's portable `Py_ssize_t`. The native source also has explicit `<stdexcept>`, an `_OPENMP` guard, and releases the GIL around the O(N^2) kernel.

**Why:** this targets the actual compiler error rather than disabling native mode or weakening the extended campaign.

### 2. Native build now self-tests

`build_ext_if_needed.py` builds with `--force`, imports the resulting module in a fresh Python process, evaluates a 32-point ring, and requires finite nonzero output.

**Why:** a successful compiler return code alone is not enough to certify that the `.pyd` imports and runs under the active Python ABI (including Python 3.14).

### 3. v0.1.0 basic G4 PASS is no longer treated as a certified physical verdict

The uploaded v0.1.0 basic results had T/S convergence disabled, and the basic dispersion gate used only modes 2, 3, 4. Fitting two coefficients (`a2`, `a4`) to three points leaves only one residual degree of freedom. In addition, the `min_phase_r2` argument existed but was not actually used by the projected-eigenvalue fit.

v0.1.1:

- requires at least four usable modes;
- adds mode 5 to the basic diagnostic run;
- evaluates the projected operator at `epsilon` and `epsilon/2`;
- filters modes by `linearization_eps_rel_error`;
- reports both `q^2` and `q^2+q^4` fit errors and the relative quartic improvement.

### 4. G1 sampling artifact reduced

The hard reparameterization gate no longer includes the current discrete thickness/ropelength estimator. Ropelength remains in the diagnostic record.

**Why:** thickness from minimum non-neighbor distances can change materially under finite resampling even when the underlying centerline is unchanged. It should not dominate a material-label invariance test.

### 5. G2 is explicitly a geometric/numerical diagnostic by default

A failed Bishop-holonomy convergence check is not reported as an SST phase-clock falsification when no measured physical phase field is present. An adaptive `N -> 2N -> 4N` refinement is attempted before declaring the geometric diagnostic failed.

### 6. Overall verdict semantics corrected

G1/G2/G3 are structural/numerical diagnostics in the present centerline-only package. G4 is the tested physical closure gate. T/S are numerical certification gates. Overall states now distinguish `CLOSURE_FAIL`, `INCONCLUSIVE`, `NUMERICALLY_INCONCLUSIVE`, and preliminary/survived states.

### 7. Extended campaign coverage

`configs/extended.json` now has `max_samples = 0` (all readable curves). Limited certification cases are selected by blind ID order rather than lexicographic filename order.
