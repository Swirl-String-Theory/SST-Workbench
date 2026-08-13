# Independence protocol v1.2

The numerical solver and candidate detector are forbidden from using external physical constants or external target values.

## Fixed numerical units

- core-radius unit = 1
- circulation unit = 1

These are definitions of nondimensionalization, not measured inputs.

## Allowed solver variables

Only dimensionless geometry, discretization, numerical tolerances, and the logarithmic cell ratio `q = ln(L/a)` may enter the solver.

## Fourier analysis variables

`max_m`, `symmetry_order`, leakage tolerances, branch-overlap threshold, and dominant-mode-weight threshold are numerical analysis controls. They do not encode an external scale.

## Range provenance

The v0.1.2 full range is restricted using only support observed in the previous internal blind numerical campaign. No external target was used to choose a center, root, or candidate location.

## Candidate prohibition

No code path may search for proximity to an externally supplied value. Global-spectrum features cannot promote candidates in v0.1.2. Fourier candidates must emerge from internal branch behavior and pass convergence gates.

## Freeze rule

Results should be hashed/frozen before any external physical interpretation or comparison is performed.
