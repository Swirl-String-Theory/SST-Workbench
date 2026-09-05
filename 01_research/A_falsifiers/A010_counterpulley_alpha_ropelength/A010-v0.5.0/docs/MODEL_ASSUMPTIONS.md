# Model assumptions -- v0.5.0

1. The background fluid is incompressible and inviscid; no external forcing is included.
2. Each channel is represented by a regularised vortex filament with fixed circulation `+Gamma` or `-Gamma`.
3. The centerline data are sampled from `ideal.txt`, knot ID `3:1:1`.
4. Tangential filament velocity is treated as a parametrisation gauge and removed for geometric shape evolution.
5. Global translation, proper rotation and one **common** cyclic relabelling are quotiented when testing relative recurrence.
6. An independent pure longitudinal relabelling of a complete closed filament is treated as gauge, not as a physical search parameter.
7. Newton--Krylov state corrections are restricted to a preregistered low-dimensional transverse Fourier/Kelvin basis; failure therefore excludes only this bounded correction space.
8. Multiple-shooting projected closure never substitutes for full Cartesian RPO closure.
9. True Floquet monodromy is forbidden unless an RPO passes full-state and resolution gates.
10. The numerical alpha target is isolated in `benchmark.py` and must not be imported before H18.
11. A future material longitudinal phase would require explicit additional core/material structure and would constitute a new physical model, not a v0.5 fitting knob.
