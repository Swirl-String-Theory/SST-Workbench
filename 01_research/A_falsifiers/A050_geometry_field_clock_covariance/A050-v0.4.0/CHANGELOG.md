# Changelog

## v0.4.0
- Converts the v0.3.2 coherent-nonstationarity observation into a frozen mechanism-discrimination campaign.
- Adds fresh deterministic holdouts, independent of the v0.3.0/v0.3.2 holdout set.
- Adds smooth-chirp, two-tone beating, phase-slip, symmetry-reduced recurrence/RPO-candidate, and residual amplitude–phase modulation tests.
- Corrects the recurrence quotient to use the mode-dependent spatial phase action `C_m -> C_m exp(-i*m*theta)`.
- Requires mechanism replication only on fresh holdouts that retain the baseline branch.
- Keeps the v0.3.0 verdict and v0.3.2 diagnostic status immutable.
- Keeps Floquet/RPO solver claims inactive; an RPO candidate only qualifies a later solver stage.

## v0.3.2
- Separates branch identity retention from stationary phase persistence.
- Adds coherent drift/reversal diagnostics while freezing the v0.3.0 verdict.
