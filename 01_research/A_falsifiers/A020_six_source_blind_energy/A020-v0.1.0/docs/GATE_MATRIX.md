# Gate matrix

| Source | Gate | Tier | Tested statement | Main observable |
|---|---|---|---|---|
| 1 Uosukainen | `U1_CROSS_SELF_SCALING` | PRIMARY_NUMERICAL_IDENTITY | cross stress is O(epsilon), self stress O(epsilon^2) | log-log slopes |
| 1 Uosukainen | `U2_TRANSPORT_MULTIPOLE` | PRIMARY_STATIC_FIELD | regularized incompressible transport source has no robust monopole/dipole | normalized M0, M1 on nested boxes |
| 2 Abe–Okuyama | `AO1_MODAL_ADDITIVITY` | MODEL_CONDITIONAL | two small deformation modes are energy-additive | nonlinear energy residual |
| 2 Abe–Okuyama | `AO6_PHASE_ERASURE` | MODEL_CONDITIONAL | fixed modal amplitudes erase relative-phase information | phase-ensemble energy CV |
| 2 Abe–Okuyama | `AO3_BOLTZMANN_GEOMETRY_PROXY` | PROXY_DIAGNOSTIC | curvature-mode powers accidentally mimic exp(-beta E) | linear fit R^2 |
| 3 Rossby | `R3_GRADIENT_LOCK_PROXY` | PROXY_DIAGNOSTIC | conditional k^2=beta_eff/U scale matches dominant curvature mode | chi_R |
| 4 Kleckner et al. | `K4_ANTIPARALLEL_CONTACT` | DIAGNOSTIC | close antiparallel strand pairs are present/absent | d_min/(2a), -t_i dot t_j |
| 4 Kleckner et al. | `K4_PERTURBATION_ROBUSTNESS` | MODEL_CONDITIONAL | hard finite-core embedding survives 0.25 rope-diameter transverse perturbations | admissible fraction, first-hit amplitude |
| 5 Hopfion | `H5_INTRINSIC_SCALE` | PRIMARY_RESEARCH_HYPOTHESIS | self-induction alone yields a finite interior homothetic minimum | E(lambda), E'', argmin |
| 5 Hopfion | `H5_CALUGAREANU_RIBBON` | PRIMARY_GEOMETRIC_IDENTITY | independent ribbon Lk agrees with Wr+Tw | absolute closure residual |
| 6 Helmholtz | `H6_CLASSICAL_NULL_CALIBRATION` | CALIBRATION | ringdown and driven amplitude/phase recover one damped oscillator | gamma, omega_d, omega_peak, phase RMSE |
| 6 Helmholtz | `H6_NONLINEAR_MIXING_CALIBRATION` | CALIBRATION | amplitude scaling separates quadratic mixing from multiplicative mixing | log-slope 2 versus 1 |

## What a FAIL means

### U1
A failure is first a numerical warning: the perturbation amplitude may not be in the linear regime, the probe geometry may be under-resolved, or the C++/Python parity audit may have failed. In the converged limit the algebraic cross/self orders should be recovered.

### U2
A converged nonzero monopole would contradict the intended no-monopole transport-stress closure. Finite boxes and finite differences can create residuals, so the EXTENDED result carries more weight than BASIC.

### AO1
Failure rejects a linear/additive modal energy decomposition for the declared regularized finite-core energy at the preregistered amplitude.

### AO6
Failure means relative phase remains observable in the declared energy. A Shannon occupation entropy is then insufficient as a complete coarse graining for that observable.

### R3
This is deliberately not a primary SST test. It asks whether a Rossby-like scale selector is numerically suggestive under a declared Gaussian-core proxy. It does not promote quasi-2D PV to a 3-D Euler invariant.

### K4
The contact gate is diagnostic. The perturbation gate is a hard-thickness geometry test, not a time-domain stability proof. A dedicated future workbench should evolve the perturbed states with an ideal/resolved finite-core solver.

### H5 intrinsic scale
This is intentionally severe. It holds the core radius and circulation fixed and asks whether **self-induction alone** has an interior minimum. A boundary minimum at lambda=1 is a FAIL of self-induction-only self-binding. It does not rule out a larger functional with independently derived tension/bending/twist terms.

### H5 ribbon
This is a numerical theorem check. Failure normally means inadequate discretization, bad offset size, or an implementation issue; do not interpret it as new physics until convergence is demonstrated.

### H6
Both H6 gates are analysis-pipeline calibration tests. They prevent a later workbench from calling a generic damped oscillator or ordinary transfer-chain intermodulation an SST-specific signal.
