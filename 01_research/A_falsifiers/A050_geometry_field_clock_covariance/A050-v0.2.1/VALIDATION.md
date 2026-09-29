# Validation v0.2.1

Required checks:

- spectral divergence ratio below the frozen numerical threshold;
- spatial exponent stability on a grid ladder;
- spatial decorrelation control;
- temporal time-shuffle control;
- Bishop-frame orthogonality and synthetic transverse-mode recovery;
- return detector refuses trivial no-departure trajectories;
- Floquet finite-difference consistency when a return is available;
- blind lexical/numeric audit over executable source, configuration, and BLIND outputs.

A gate may report an indeterminate state when its prerequisite is absent. This is deliberate and prevents interpreting a multiplier without a recurrent base trajectory.


## v0.2.1 long-observation validation
- Gate thresholds are frozen from v0.2.0 and checked by `test_v021.py`.
- `time_step` and `sample_every` are unchanged.
- A Kelvin pass therefore requires the pre-existing phase-coherence and phase-cycle criteria, not a relaxed post-hoc threshold.
- Floquet remains indeterminate unless the pre-existing departure/return criteria identify a recurrence.

- The expensive pressure-field gates intentionally retain the v0.2.0 horizon; only the unresolved Kelvin/Floquet observation horizons are extended.
