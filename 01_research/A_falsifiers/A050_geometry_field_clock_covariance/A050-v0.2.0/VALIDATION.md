# Validation v0.2.0

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
