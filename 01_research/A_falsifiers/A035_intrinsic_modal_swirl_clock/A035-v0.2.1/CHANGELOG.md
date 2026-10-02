# Changelog

## v0.2.1 — Numerical-Certification / Parameterization-Invariance Hotfix

This release changes **numerical certification**, not SST physics.

The v0.2.0 BASIC campaign showed that a global `FAIL_STAGE_A_NO_RECURRENT_SHAPE_CLOCK` was too strong: only 3/49 carriers passed the strict long-horizon geometry gate, and all three predeclared high-information carriers failed to remain certifiable to `T=24`.

### Fixed: coverage-aware negative verdicts
- A global negative Stage-A verdict now requires:
  - at least 80% geometry-valid carriers in BASIC/EXTENDED;
  - at least 20 valid carriers;
  - **all predeclared priority carriers geometry-valid**.
- Otherwise the gate is:
  - `INDETERMINATE_STAGE_A_INSUFFICIENT_VALID_COVERAGE`.
- Focus runs use 1/1 coverage; the resolution trio uses 3/3 coverage.

### Fixed: parameterization-invariant modal observable
Every Stage-A snapshot is analysis-only canonicalized by:
1. uniform closed-curve arclength resampling;
2. cyclic parameter-origin alignment;
3. rigid Kabsch alignment;
4. normal projection.

Thus POD no longer follows bead-index drift created by the tangential mesh gauge.

### Improved tangential redistribution
- Replaced the default target-point projection controller with direct segment-length feedback:
  `alpha[i+1]-alpha[i] = -k (ell[i]-mean(ell))`.
- Applies only `u_mesh = alpha t_hat`.
- Optional legacy `target_projection` method remains for audit.
- RMS mesh speed is capped relative to physical Biot-Savart RMS speed.
- Strict `ds_cv <= 0.20` certification gate is retained; it is **not relaxed**.

### New mesh-gauge certification
A provisional recurrent Stage-A mode is replayed only on that anonymous carrier with:
- lower redistribution gain (`0.6 x nominal`),
- higher redistribution gain (`1.4 x nominal`).

The frozen nominal mode must remain recurrent and its period, closure and amplitude must remain within predeclared spread gates. Only then is it promoted to `stage_a_candidates.json` and allowed into Stage B.

### High-information carrier coverage
The following source patterns are predeclared before blinding:
- `knot_6.3_final`,
- `link_4.2.1_final`,
- `link_9.2.20_final`.

The blind scorer sees only a `certification_priority` role flag, never the source identity.

### Progress logging
Long branches now emit anonymous per-candidate progress:
`[stage_a 017/147] ... t=... ds_cv=... stop=... mesh/phys=...`.

### Chain
BASIC is now 9 stages:
prepare -> nominal Stage A -> provisional analysis -> low/high mesh-gauge replays -> gauge certification -> material/fixed Stage B -> final analysis.

### Retained safeguards
- `T_A=24` BASIC, `T_A=36` EXTENDED.
- absolute `discovery_time=1.2`.
- RK4.
- hard `dt ~ ds^2` step-cap policy; no hidden timestep coarsening.
- `py::ssize_t` Windows/MSVC guard.

## v0.2.0 — Long-Horizon Mesh-Stabilized Recurrence Gate

Introduced Stage-A-first recurrence, `-/0/+` probe arms, natural + odd modal channels, tangential mesh stabilization, multi-return closure, fixed absolute discovery window, and candidate-only material/fixed Stage B.
