# Preregistration

Primary self-confinement metrics are fixed before reveal and all are lower-better:

1. `contact_survival_deficit`
2. `initial_relative_equilibrium_residual`
3. `shape_auc`
4. `rpo_residual`
5. `max_real_growth_positive`

For a pair the median anonymous log-ratio determines A/B/TIE with a 3% tie margin. Source/family/condition labels are inaccessible during scoring.

Pressure and gravity are **not** included in the primary self-confinement score. Their gates are evaluated independently after seal:

- active central pressure must be more negative than the zero-thread-circulation null;
- `1/r` and `1/r^2` pressure fits compete without target injection;
- a pressure deficit with a better `1/r^2` fit is explicitly reported as `PRESSURE_DEFICIT_ONLY_GRAVITY_NOT_CLOSED` or `FAVORS_1_OVER_R2_NOT_NEWTONIAN`.

Absolute circulation is not allowed to count as a stabilizing parameter unless the dimensionless circulation-similarity gate fails for a physically justified reason; pure Euler scaling predicts time rescaling at fixed beta.
