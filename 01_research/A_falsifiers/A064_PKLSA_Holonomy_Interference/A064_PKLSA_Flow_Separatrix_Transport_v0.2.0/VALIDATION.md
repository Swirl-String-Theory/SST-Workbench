# A064 v0.2.0 Validation (2026-10-15)

**Software regressions:** 17/17 PASS (legacy A064 and v0.2.0 spectral Euler extension).

**Positive analytic Euler reference:** periodic Arnold–Beltrami–Childress field, with `curl(v)=v` and RK4 steady flow to machine precision.

**Independent numerical controls:** nontrivial knotted initial state evolves, divergence-free FFT projection, energy and helicity drifts monitored; RK4 step-halving exhibits improved endpoint accuracy.

**Self-contained NPZ data:** 3 original raw geometries, 3 legacy stationary NPZs, 3 evolved 13-frame Euler NPZs, per-input and per-NPZ SHA-256 metadata, candidate discovery source+mesh seals.

**Evolved source:** `geometry_initialized_periodic_3d_euler_model`, never promoted to independent experimental or direct physical PKLSA measurement.

## 13-frame dynamic screening

| Topology | max relative energy drift | max spectral divergence | normal flux / U | tracer crosses | enstrophy stretch identity rel L2 |
|---|---:|---:|---:|---:|---:|
| `3_1` | 3.6366e-10 | 1.4820e-14 | 0.5537 | 40/218 | 0.07793 |
| `5_2` | 1.5894e-09 | 1.7110e-14 | 0.3964 | 54/219 | 0.06782 |
| `6_1` | 8.9445e-10 | 1.7992e-14 | 0.4905 | 47/218 | 0.16935 |

All **specific selected enstrophy isosurfaces** are classified `PERMEABLE_NONMATERIAL_FEATURE` at this model scale. All physical/model certification gates remain `UNRESOLVED`; the existence or absence of an actual invariant separatrix is not inferred.

**Two-grid `3_1` preview:** `N=24` vs `N=32` L2 velocity differences 0.01167 initially and 0.01859 finally. This is *not* convergence proof; it measures change between grids.

**Original A064 v0.1.1 output:** preserved only as historical baseline in documentation and frozen NPZs. The 13-frame v0.2.0 values supersede the earlier four-frame exploratory values.

**Framework:** v1.0.7 `CANONICAL_FROZEN` is the verified intended baseline from Google Drive, but its FREEZE/CERTIFY was NOT executed against this prototype. No `_BLIND.zip` or `CERTIFIED` is claimed.
