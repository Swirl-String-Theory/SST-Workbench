# Model assumptions and falsification boundaries

1. The hydrodynamic backend is incompressible, inviscid **filament** Biot–Savart with a regularization length. It is not a complete volumetric finite-core Euler solver.
2. The bundled `ideal_3_1_1.txt` geometry supplies a reproducible trefoil centerline seed.
3. Tangential marker velocity is removed for geometric shape evolution where the inherited RPO machinery requires the centerline gauge quotient.
4. No reconnection rule is implemented.
5. Phase-I Rankine quantities are laboratory-paper benchmarks; SST-scale substitutions are explicitly classified as diagnostics.
6. Phase-II frozen trefoil eigenmodes do not become Floquet eigenmodes unless K6 finds an accepted RPO.
7. Phase-III resonance candidates are selected from numerical frequencies without imposing a desired four- or six-wave conclusion.
8. Phase-IV is a finite-time conservative/unforced transfer experiment; it cannot by itself establish a stationary turbulent inertial range.
9. K14 protects only against explicit numerical target leakage in the scientific Python/C++ sources. It does not prove conceptual independence from every possible modelling choice.
10. A future volumetric finite-core SST implementation should preserve the gate API so results can be compared model-for-model without changing the acceptance logic.
