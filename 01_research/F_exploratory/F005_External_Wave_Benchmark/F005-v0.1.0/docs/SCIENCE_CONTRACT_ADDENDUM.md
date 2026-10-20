# Science-contract addendum — F005 v0.3.0

**Observation domain:** robot-driven free-surface sloshing. Raw sources immutable.

**Primary measured observables:** `a(t)` in m s^-2, `eta(t)` in mm, explicit time vector in seconds. Physical model uses eta converted to meters.

**Audit gate P5:** structural split PASS requires exact unique IDs 0..9821, expected partition counts, metadata length match, no nonfinite inputs or exactly repeated input waveforms across partitions. This is only a *structural* condition; a full family-disjoint and blind-validation PASS needs independently justified family labels and a newly registered, frozen heldout split. Current candidate remains **REVIEW**, never certified PASS.

**Exploratory ARX baseline:** `eta[n+1] = A eta[n] + B eta[n-1] + C (dt)^2 a[n]` in meters. A, B, C dimensionless. Train coefficients with candidate train only; one-step teacher-forced validation with candidate validation only, no test/OOD target values. Complex, stable characteristic roots yield a diagnostic ringdown frequency, not an Euler-mode proof.

**P6 Euler closure:** NOT RUN / ARX DEVELOPMENT ONLY. Required Euler reference needs fluid height, tank geometry, boundary conditions, forcing-to-surface transfer, validation uncertainty and independent implementation.

**P7 PKLSA independence:** NOT RUN. No SST clocks, swirl density or canonical SST constants are inserted as fitted quantities.

**P8 physical claim:** UNRESOLVED. The benchmark is not evidence of a propagating bulk inertial wave, vortex torsion, or Kelvin mode.
