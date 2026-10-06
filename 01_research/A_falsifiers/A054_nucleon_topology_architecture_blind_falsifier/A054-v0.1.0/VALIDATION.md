# Validation — build snapshot

Validation performed in the ChatGPT execution container on 2026-10-06.

- Python reference tests: **7 passed**.
- Native-equivalence test: **1 skipped**, because `pybind11` was not installed in the offline container.
- Analytic `T(3,3)` test at 360 points/component: pairwise linking approximately `-1.00008` for every pair (orientation sign is conventional; unit magnitude is the gate).
- Analytic Borromean closed-braid test at 360 points/component: maximum absolute pairwise numerical linking approximately `3.9e-5`.
- Generic local connected-sum decorator test: PASS for both `T(3,3)` and Borromean skeletons using a nontrivial source knot; pairwise skeleton-linking drift stayed below `0.01`.
- Blind partial preparation without a Workbench: PASS; exactly three anonymous analytic controls prepared and `scientific_ready=false`.
- Isolated blind-runner semantic leak scan: PASS.
- Blind runner executes without the private identity map and emits/seals anonymous observables: PASS.
- Reveal verifies the blind seal and joins identity without recomputing scientific observables: PASS.

No real PKLSA centerline was fabricated in this container. Production PKLSA provider strata remain a local-Workbench execution because the source archives are not mounted here.
