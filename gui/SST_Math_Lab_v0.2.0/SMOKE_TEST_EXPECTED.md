# v0.2.0 smoke-test reference

These values are implementation reference values for the default generated `T(2,3)` geometry. They are **not SST empirical predictions** and should not be promoted to canonical constants.

Reference settings used for the core calculation:

- `R = 2.5`
- `a = 1.0`
- physical scale = `r_c`
- geometry samples = 1200
- physics samples = 128 for this reference calculation
- finite-core radius = `1.0 r_c`
- circulation = `Gamma_SST`
- pressure probe step = `0.25 a_core`
- stability ceiling = `M = 4`
- perturbation = `0.02 a_core`

Expected approximate values:

- `L/r_c = 36.93933`
- `max(kappa r_c) = 0.52801`
- `min(tau r_c) = -3.85561`
- `max(tau r_c) = 0.043036`
- mean finite-core Biot speed ≈ `7.7149e5 m s^-1`
- max finite-core Biot speed ≈ `1.4645e6 m s^-1`
- max shape speed ≈ `8.3555e5 m s^-1`
- max dynamic-pressure magnitude ≈ `7.5070e5 Pa`
- max absolute pressure-Poisson source ≈ `7.89e35 Pa m^-2`
- relative divergence RMS ≈ `1.69e-3`
- raw transport-frame holonomy ≈ `-2.0758 rad`

Independent Python/Numpy replication of the centered reduced stability calculation at 128 physics points gives approximately:

- `max Re(lambda) = 2.5985e20 s^-1`
- epsilon-ladder max-growth values ≈ `[2.59863e20, 2.59851e20, 2.59805e20] s^-1`
- relative epsilon-ladder spread ≈ `2.23e-4`

The analytic trefoil is not a relaxed finite-core relative periodic orbit. Therefore a positive frozen-geometry growth rate here is expected to be treated as a diagnostic, not as a final stability statement about an SST particle candidate.
