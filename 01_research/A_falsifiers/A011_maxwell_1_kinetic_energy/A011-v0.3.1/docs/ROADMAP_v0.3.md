# v0.3 implementation status — Boltzmann/Verlinde statistical closure

The former v0.3 plan for a true physical mode solver has been moved to `ROADMAP_v0.4.md`.  The intervening v0.3 release implements the statistical/falsifier layer motivated by the Boltzmann 1877 and Verlinde 2010/2011 analyses.

Implemented:

1. combinatorial complexion/permutability counting;
2. fixed-constraint maximum-multiplicity test;
3. Boltzmann occupation-law fit and inferred temperature;
4. optional detailed balance;
5. `S=k_B ln N_accessible` from externally sampled state counts;
6. microcanonical `dS/dE` temperature;
7. entropy-gradient force;
8. independent pressure/hydrodynamic force comparison;
9. scalar entropy/pressure integrability test;
10. optional Verlinde entropy-displacement, area-law, equipartition, inferred-`G`, inverse-square and potential/entropy gates;
11. explicit claim switches preventing speculative bridges from becoming automatic SST assertions;
12. synthetic PASS/FAIL datasets and ready-made Windows `.cmd` scripts.

Not implemented because the present centerline data cannot justify them:

- physical SST microstate sampler;
- physical knot energy functional;
- automatic equilibrium or ergodicity assumption;
- finite-core/core-mode state counting;
- relativistic holographic/Einstein reconstruction.
