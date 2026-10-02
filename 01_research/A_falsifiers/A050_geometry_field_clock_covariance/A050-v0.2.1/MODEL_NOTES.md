# Model notes v0.2.1

- All dynamics are dimensionless.
- The velocity field is normalized by its own RMS magnitude before the pressure-Poisson scalar closure is solved.
- The temporal-memory gate compares the measured correlation time and one-step correlation against independently time-shuffled probe series.
- The transverse-mode gate is a geometry/dynamics diagnostic. It does not assign an absolute wave speed.
- The Floquet gate is conditional on an observed nontrivial return and has an explicit finite-difference convergence check.
- A missing return is an indeterminate Floquet result, not a failed stability claim.


## v0.2.1 protocol amendment
This patch changes observation horizon only. It does not retune any scientific acceptance threshold from v0.2.0. Default dynamics are observed for 320 steps; the independent recurrence search is observed for 640 steps.
