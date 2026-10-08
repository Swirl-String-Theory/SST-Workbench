# A016 migration analysis: v0.1.1 -> v0.2.0

## What v0.1.1 already established

The supplied v0.1.1 package was structurally sound for a static-centerline falsifier. It already separated Helmholtz statements from SST interpretation and correctly refused to infer material-line persistence, time-dependent flux conservation, or torsion closure from static knot geometry.

The included completed campaigns contained 49 inputs. In the normal run, H1 convergence, H2 holonomy, and H4 symmetry passed for all 49; H0 failed for one input; H3 relative equilibrium passed for 3 and failed for 46. In the extended run, H0-H2 and H4 passed for all 49, while H3 again passed for 3 and failed for 46. The identity of the three prior H3 passes is intentionally not repeated in the public migration note, so a new blind run does not receive target-bearing filename hints from the source tree. The old frozen/reveal artifacts remain the provenance source for those identities.

## Why v0.2.0 is not a threshold retune

No v0.1.1 threshold is loosened in order to rescue failed centerlines. H0-H4 retain the same numerical thresholds. v0.2.0 changes the architecture and adds logically distinct tests.

## Main scientific expansion

The central new distinction is between:

1. **material vorticity support** — the Lagrangian population initially carrying nonzero vorticity;
2. **exterior potential sector** — regions with locally zero vorticity that may still carry nonzero velocity, circulation periods, pressure response, and kinetic energy.

P0-P2 use an exact incompressible affine deformation as a theorem-level control of the Cauchy vorticity formula. P3-P6 then ask what the same finite-core/filament representation predicts outside the source support.

## Framework migration

v0.1.1 shipped its own virtual environment, compiled extension, caches, and prior run outputs. v0.2.0 is a clean thin instance of SST Falsifier Framework v1.0.6. Backend construction, protocol freezing, HMAC opaque IDs, reveal commitments, provenance, deterministic packaging, and report generation are delegated to the frozen framework; experiment-specific equations and kernels remain local to A016.

## Continue-after-failure semantics

A serial gate chain would suppress useful later measurements after the first physical failure. v0.2.0 therefore uses a fan-out DAG. G0/G1/G2 are infrastructure/reference prerequisites; H0-H4 and P3-P6 are siblings after those prerequisites. A FAIL in H3, for example, does not prevent P3-P6 from running. P0-P2 are analytic controls independent of the external knot source. B0 is independent backend certification. A scientific FAIL is an outcome, not a process error.
