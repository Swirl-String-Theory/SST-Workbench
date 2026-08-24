# SST Material-Coordinate / Phase-Shift EFT Falsifier

**Version:** 0.1.0  
**Overall:** **FAIL**  
**Samples analyzed:** 3  

## Gate counts

| Gate | PASS | FAIL | SKIP |
|---|---:|---:|---:|
| G1_REPARAM | 2 | 1 | 0 |
| G2_PHASE | 2 | 1 | 0 |
| G3_REDUNDANCY | 3 | 0 | 0 |
| G4_DISPERSION | 2 | 0 | 1 |
| T_CONV | 0 | 0 | 3 |
| S_CONV | 0 | 0 | 3 |

## Interpretation

- G1: centerline-accessible surrogate of material relabeling.
- G2: gauge invariance + convergence of candidate Bishop-frame holonomy; no measured physical SST phase is assumed.
- G3: total-derivative and integration-by-parts operator redundancy.
- G4: regularized finite-core Biot-Savart perturbation dynamics; fits `omega^2 = a2 q^2 + a4 q^4`.
- T/S: separate numerical certification with RK4, `dt proportional to ds^2`, fixed final time and arclength reparameterization.

PASS means the preregistered closure survived the gate at the configured tolerance; it is not confirmation of SST. FAIL falsifies the tested closure/hypothesis subject to the numerical-certification gates.