# F005 v0.4.0 science contract - predeclared development gates

Source: robot-executed sloshing archive (Zenodo DOI 10.5281/zenodo.20039757). Time base from `time_vector.csv`; elevations in publisher's mm converted to SI meters; accelerations in m/s^2. Does NOT test Kelvin filaments, bulk inertial wave modes or a physical PKLSA solution.

## Locked observables / time direction

Discrete closed-loop-free conditional predictor:

$$
\hat\eta_{n+1}=A\hat\eta_n+B\hat\eta_{n-1}+C(\Delta t)^2a_n.
$$

For each anchor `n0`, only `eta[n0-1]` and `eta[n0]` initialize the prediction, with the future measured/commanded forcing `a[n]` treated as **known exogenous input**. The recursion must not read `eta[n0+1:]`. Time in seconds; A, B, C are dimensionless.

1. **G0 - Input provenance:** v0.3 SHA256 locks for prior pilot JSON, candidate split CSV and metadata CSV reproduce; numerical arrays have expected shapes and time axis. Failure BLOCKS.
2. **G1 - P5b:** check waveform-family candidates using only accelerations; duplicate forcing and near-shape similarity are diagnostic. Missing publisher-defined true family IDs means group separation UNRESOLVED.
3. **G2 - P6a:** compute conditional no-teacher-forcing rollouts at prespecified anchors 0.004, 1.5 and 2.8 s, horizons 0.1/0.5/1/2/3 s. Only STANDARD_VALIDATION elevations may be accessed. Compare to 2 no-fit baselines.
4. **G3 - P6b:** report horizon-wise and anchor-wise RMSE vs persistence and tangent extrapolation; do not claim model superiority if long-horizon performance fails.
5. **G4 - Holdout:** TEST/OOD responses are not read, hashed, plotted or used for selection. TEST/OOD *input accelerations* may be used solely to search inter-partition near duplicates.
6. **G5 - Physics:** Euler mode baseline NOT RUN; PKLSA NOT RUN; physical SST claim UNRESOLVED. No certification regardless of P6 outcome.

Stop/invalidate for wrong source hashes, invalid split indices, unexpected NPY shape/dtype, time-axis inconsistency, unexpected v0.3 coefficients, nonfinite data, or exhausting search budgets. Unexamined large waveform buckets remain explicit audit limitations, not evidence of absence.

No hyperparameter changes can be made after seeing holdout outputs. Any future blind campaign must create an explicit source-defined group-disjoint split and freeze independent model predictions **before** revealing test observations.