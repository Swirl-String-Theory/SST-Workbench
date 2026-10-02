# Preregistration protocol

Freeze the following **before** inspecting held-out physical results:

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
12. whether a purported finite intercept is called only an `activation` threshold or has an independently derived discrete-state justification.

## Decision hierarchy

### Physical falsifier

A campaign may trigger a physical falsifier when, under a preregistered model and empirical limit:

- a claimed positive gap is contradicted by its own `A -> 0` energy branch;
- the declared discrete spectrum predicts a thermodynamic contribution above a preregistered empirical bound;
- the declared occupations/couplings imply a spectroscopic signal above a preregistered empirical bound.

### Numerical / closure failure

These invalidate the numerical claim or closure before a physical comparison is trustworthy:

- low-energy spectrum/coupling does not converge;
- energy drift exceeds tolerance;
- twist is declared without a material frame;
- core modes are declared without finite-core resolution;
- writhe is counted as an independent energy channel without an explicit independence proof.

### Non-falsification

`NO_FALSIFIER_TRIGGERED_NOT_VALIDATION` is not a positive confirmation. It means only that no implemented preregistered gate failed on the supplied data.
