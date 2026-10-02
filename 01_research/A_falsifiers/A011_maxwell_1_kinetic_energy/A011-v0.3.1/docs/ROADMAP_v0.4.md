# Roadmap v0.4 — true physical mode/state sampler adapter

v0.3 deliberately stops before inventing a physical SST energy functional or accessible-state measure.  The next high-value release should automate the physical inputs that are still manual.

1. Import a declared finite-core SST energy functional `E[Q]` without fitting it to desired spectra.
2. Construct the projected Hessian and generalized inertia operator to obtain physical normal modes.
3. Generate amplitude scans, modal gaps and encounter energy transfer directly from the solver.
4. Add material-frame twist only when a material frame is actually resolved.
5. Add core modes only with a resolved finite core.
6. Implement invariant-preserving MCMC / deterministic orbit sampling of accessible knot microstates.
7. Measure mixing/autocorrelation times and effective sample sizes before applying Boltzmann statistics.
8. Generate `state_distribution.csv`, `state_occupations.csv` and `state_counts.csv` automatically from frozen invariant sectors.
9. Compute independent pressure/stress forces without accessing the state-count output.
10. Split sampler and force pipeline into separate held-out stages so the entropy-force equality can be genuinely blind.
11. Add resolution/coarse-graining ladders for `dS/dx` and microcanonical `dS/dE`.
12. If warranted, extend the scalar 1-D gate to a 3-D entropy field reconstruction and closed-loop test `oint grad S . dl = 0`.
