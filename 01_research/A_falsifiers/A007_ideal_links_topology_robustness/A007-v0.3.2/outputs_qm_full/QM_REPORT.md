# SST ideal links — QM-readiness campaign v0.3.2

- Links completed: **5**
- Preset: **qm_full**
- Backend: **cpp**
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Scientific boundary

This campaign does not derive quantum mechanics. Quick/diagonal Hessians are screening-only. Pairwise-zero links require higher link invariants even when their catalog identity is known.

## Highest-readiness candidates

| link_id   | common_name     | best_signs   |   readiness_level | readiness_label              |   relative_equilibrium_score |   primary_gradient_norm |   primary_gradient_cancellation_ratio |   primary_negative_modes | hessian_scheme   |   symplectic_rank |   symplectic_dimension |
|:----------|:----------------|:-------------|------------------:|:-----------------------------|-----------------------------:|------------------------:|--------------------------------------:|-------------------------:|:-----------------|------------------:|-----------------------:|
| L4a1      | nan             | --           |                 1 | pair-linking-sector-resolved |                     0.147007 |                13.5807  |                              0.843864 |                        4 | full-central     |                20 |                     20 |
| L2a1      | nan             | --           |                 1 | pair-linking-sector-resolved |                     0.177857 |                26.0766  |                              0.926959 |                       10 | full-central     |                16 |                     18 |
| L6n1      | nan             | -+-          |                 1 | pair-linking-sector-resolved |                     0.184612 |                 8.89077 |                              0.687203 |                       11 | full-central     |                30 |                     30 |
| L6a4      | Borromean rings | ---          |                 1 | pair-linking-sector-resolved |                     0.186292 |                 7.39913 |                              0.669349 |                       11 | full-central     |                30 |                     30 |
| L7n2      | nan             | --           |                 1 | pair-linking-sector-resolved |                     0.264883 |                12.8093  |                              0.78225  |                        5 | full-central     |                20 |                     20 |

## Pairwise-linking insufficiency flags

| link_id   | common_name     |   components | higher_linking_required   | higher_linking_computed   |
|:----------|:----------------|-------------:|:--------------------------|:--------------------------|
| L6a4      | Borromean rings |            3 | True                      | False                     |
| L7n2      | nan             |            2 | True                      | False                     |

## v0.3.2 interpretation rules

- Topology uses an independent higher-resolution sampling grid.
- Every 2^m circulation assignment is retained; candidate automorphisms do not quotient sectors.
- Energy terms use preregistered fixed reference scales rather than per-sector baselines.
- `spectrally_stable_claim=true` is possible only with a full off-diagonal Hessian.
- L6a4 is catalogued as the Borromean rings; its Milnor triple invariant is not computed here.