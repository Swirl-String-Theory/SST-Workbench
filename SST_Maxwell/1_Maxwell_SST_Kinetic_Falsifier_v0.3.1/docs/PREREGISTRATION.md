# Preregistration protocol — v0.3.1

Freeze the following **before** inspecting held-out physical results.

1. knot geometry/version and finite-core prescription;
2. mode basis and family-classification algorithm;
3. amplitude normalization used in gap scans;
4. zero-mode removal procedure for translation/global orientation;
5. material-frame definition for twist;
6. core variables and spatial resolution for core modes;
7. interaction family and drive-energy grid;
8. coupling significance threshold and minimum transfer fraction;
9. observation/equilibration time window;
10. convergence tolerance and required resolution ladder;
11. empirical thermodynamic and spectroscopic limits and their provenance;
12. whether a finite intercept is called only an `activation` threshold or has an independently derived discrete-state justification;
13. **accessible-state measure** used for Boltzmann counting;
14. the invariant sector held fixed during state counting: topology, circulation, helicity and any additional solver invariants;
15. energy and position binning, sampling measure and burn-in/mixing rule;
16. whether particles/configurations are labelled in the microscopic complexion count and how declared degeneracies are handled;
17. `temperature_K` source: imposed bath, independently inferred microcanonical temperature, or another declared observable;
18. held-out positions used for `dS/dx` and finite-difference stencil;
19. the independent hydrodynamic force/pressure pipeline used for the entropy-force comparison;
20. all `research_claims` booleans;
21. Boltzmann fit tolerance, minimum `R^2`, detailed-balance tolerance;
22. entropic-force, integrability, screen/equipartition, inverse-square and entropy-displacement tolerances;
23. whether a holographic screen is being asserted at all.  If not, keep that claim `false`.

## Anti-leakage rule

`state_counts.csv` and `state_occupations.csv` must be generated without reading or optimizing against `force_reference.csv`, spectroscopy limits, or the final gate outcomes.  Hyperparameters selected after observing the held-out force are invalid for a blind campaign.

## Decision hierarchy

### Physical falsifier

A campaign may trigger a physical falsifier when, under a preregistered model and empirical limit:

- a claimed positive gap is contradicted by its own `A -> 0` branch;
- a declared discrete spectrum predicts thermodynamic response above a preregistered bound;
- declared occupations/couplings imply a spectroscopic signal above a preregistered bound.

### Research-closure failure

Only an explicitly enabled optional bridge can fail:

- Boltzmann equilibrium law / detailed balance;
- entropy-gradient force equals independent SST pressure force;
- pressure/temperature integrability;
- Verlinde entropy-displacement coefficient;
- holographic area law / inferred `G` / equipartition;
- inverse-square radial law;
- potential/entropy-per-bit relation.

A bridge failure does not automatically falsify the underlying Euler pressure dynamics.

### Numerical / closure failure

These invalidate the numerical claim before a physical comparison is trustworthy:

- spectrum/coupling does not converge;
- energy drift exceeds tolerance;
- twist declared without material frame;
- core modes declared without finite-core resolution;
- writhe counted as an independent energy channel without an independence proof.

### Non-falsification

`NO_FALSIFIER_TRIGGERED_NOT_VALIDATION` means only that no implemented preregistered gate failed.
