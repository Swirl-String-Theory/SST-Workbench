# Changelog

## v0.1.0 — 2026-10-20 — DEVELOPMENT

- Replaced invalid velocity-field Legendre transform by material-coordinate canonical momentum.
- Re-derived incompressible Euler equations by varying a Jacobian-constrained action.
- Added correctly scoped pressure-Poisson, energy, vorticity and Kelvin relations.
- Separated optional, dimensionally consistent Euler-Poincare `H^1`/Euler-alpha regularization from the exact Euler baseline.
- Segregated helicity, Coulomb, gravity, vortex-clock and mass hypotheses rather than declaring them derived.
- Added reproducible 22-test analytical regression suite (no 3D vortex dynamics).
- Preserved the historical VAM-5 PDF unchanged.
