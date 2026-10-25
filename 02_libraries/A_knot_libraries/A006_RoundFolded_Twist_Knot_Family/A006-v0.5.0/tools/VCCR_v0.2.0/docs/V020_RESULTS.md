# VCCR v0.2.0 — Executed independent Euler qualification

Execution date: 2026-10-23; Python >=3.10 + NumPy; retained original user-supplied A006 VCCR v0.1.0 code.

## Summary
- Regression suite: **18/18 PASS**, including original 7/7.
- G1 exact affine Euler RK4 material tracer + finite-difference Euler momentum/divergence/pressure Poisson: **PASS**.
- G2 deliberately broken angular velocity law: **REJECTED**, negative-control check **PASS**.
- G3 both circular and elliptic material sections: **PASS area-equivalent closure**; elliptic is NOT circular.
- G4-G8 native knotted physics: **NOT RUN / UNRESOLVED**.
- External native ingestion: complete synthetic schema, `GN0..2 PASS` for test fixture only; PDE/knotted flow NOT RUN.

## Numerical benchmark (dimensionless, NOT SST finite-core)

| Length stretch λ | Measured a_eff(t)/a_eff(0) | Predicted λ^-1/2 | Relative radius error | Volume error | Circulation error |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.000000000000 | 1.000000000000 | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| 1.25 | 0.894427191004 | 0.894427191000 | 4.302e-12 | 8.604e-12 | 8.632e-12 |
| 1.5 | 0.816496580938 | 0.816496580928 | 1.241e-11 | 2.482e-11 | 2.488e-11 |
| 2 | 0.707106781219 | 0.707106781187 | 4.651e-11 | 9.302e-11 | 9.311e-11 |
| 3 | 0.577350269333 | 0.577350269190 | 2.488e-10 | 4.976e-10 | 4.977e-10 |
| 4 | 0.500000000391 | 0.500000000000 | 7.827e-10 | 1.565e-09 | 1.566e-09 |

Maximum relative residuals across sampled λ: core radius 7.827e-10; material volume 1.565e-09; Kelvin circulation 1.566e-09.
Maximum sampled Euler momentum residual: 8.036e-11 (dimensionless); pressure Poisson residual 1.060e-09 (dimensionless).

## Convergence (RK4)

| Steps / time unit | Steps at λ=2 | Relative volume error |
|---:|---:|---:|
| 25 | 44 | 3.3351e-07 |
| 50 | 87 | 2.2803e-08 |
| 100 | 174 | 1.4561e-09 |
| 200 | 347 | 9.3020e-11 |
| 400 | 694 | 5.8429e-12 |

Halving RK4 integration step reduces residual by approximately 15–16x at these refinements, consistent with 4th-order global time integration.

## Conditions, uncertainties and scope
- Exact Euler benchmark is a linear unbounded field with uniform axial vorticity; vorticity is not localized inside the chosen material ring. This is not a finite-core isolated vortex.
- `a_eff=sqrt(A/pi)` is area-equivalent: the elliptic example has the same area/radius closure while its major/minor boundary radii differ.
- No knot dynamics, topology invariants, reconnection gates, physical core reach, independent native vorticity flux, or Swirl Clock frequency were measured.
- Original XYZ seeds are in arbitrary coordinates. Cross-file SI length calibration, shared physical material volume, and tight-tube geometric thickness were not measured.
- This validates a numerical implementation of established Euler/Kelvin tube conservation, not an SST physical discovery.

## Canonical conditional reference (not fitted)

```
rc = 1.40897017e-15 m
v_swirl = 1.09384563e6 m/s
R_d(3_1) = 16.3714672385  (diameter convention; numerical reference)
L0 = 4.6133817956357553e-14 m
V0 = 2.877218654223102e-43 m^3
Gamma0 = 9.683619203488876e-9 m^2/s
omega0 = 1.552689e21 s^-1
```

## Recorded gates

| Gate | Recorded status |
|---|---|
| `G0_v010_analytic` | `PASS_REFERENCE_7_TESTS_SEPARATELY` |
| `G1_independent_exact_Euler_benchmark` | `PASS` |
| `G2_negative_control` | `PASS` |
| `G3_material_cross_section_affine` | `PASS` |
| `G4_native_knotted_solver` | `NOT_RUN` |
| `G5_independent_native_vorticity_flux` | `NOT_RUN` |
| `G6_spatial_temporal_convergence_native` | `NOT_RUN` |
| `G7_topology_and_clearance` | `NOT_RUN` |
| `G8_SST_clock` | `NOT_RUN` |

## Immediate next experiment
Attach a real finite-core Euler/PKLSA solver to `run_vccr.cmd NATIVE`: material-tagged cross-section markers, sampled Euler velocity and pressure, independent vorticity flux integration, spatial and temporal convergence, and independent topology/clearance gating. Keep knot-specific physical claims unresolved until measured.

## Sources
A. J. Chorin and J. E. Marsden (1993), A Mathematical Introduction to Fluid Mechanics, 3rd ed., Springer, doi:10.1007/978-1-4612-0883-9.
A. J. Majda and A. L. Bertozzi (2002), Vorticity and Incompressible Flow, Cambridge University Press, doi:10.1017/CBO9780511613203.
J. Cantarella, R. B. Kusner, and J. M. Sullivan (2002), On the Minimum Ropelength of Knots and Links, Invent. Math. 150, 257–286, doi:10.1007/s00222-002-0234-y.
LaTeX `\bibitem` entries: `references.tex` in package.
