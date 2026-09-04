# SST ideal links — QM-readiness campaign v0.3.3

- Links completed: **18**
- Preset: **qm_quick**
- Backend: **cpp**
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Scientific boundary

This campaign does not derive quantum mechanics. Quick/diagonal Hessians are screening-only. Pairwise-zero links require higher link invariants even when their catalog identity is known.

## Highest-readiness candidates

| link_id   | common_name     | best_signs   |   readiness_level | readiness_label              |   relative_equilibrium_score |   primary_gradient_norm |   primary_gradient_cancellation_ratio |   primary_negative_modes | hessian_scheme   |   symplectic_rank |   symplectic_dimension |
|:----------|:----------------|:-------------|------------------:|:-----------------------------|-----------------------------:|------------------------:|--------------------------------------:|-------------------------:|:-----------------|------------------:|-----------------------:|
| L4a1      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.150946 |                 2.38278 |                             0.281825  |                        0 | diagonal-central |                12 |                     12 |
| L2a1      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.177469 |                 3.5988  |                             0.343902  |                        1 | diagonal-central |                10 |                     10 |
| L6n1      |                 | -+-          |                 1 | pair-linking-sector-resolved |                     0.189598 |                 1.01    |                             0.0886592 |                        0 | diagonal-central |                18 |                     18 |
| L6a4      | Borromean rings | -++          |                 1 | pair-linking-sector-resolved |                     0.201089 |                 1.58328 |                             0.137783  |                       10 | diagonal-central |                18 |                     18 |
| L7a1      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.204557 |                 1.00016 |                             0.0876565 |                        0 | diagonal-central |                12 |                     12 |
| L6a3      |                 | -+           |                 1 | pair-linking-sector-resolved |                     0.210519 |                 2.55633 |                             0.273064  |                        0 | diagonal-central |                12 |                     12 |
| L7a2      |                 | -+           |                 1 | pair-linking-sector-resolved |                     0.216542 |                 1.20798 |                             0.0992334 |                        0 | diagonal-central |                12 |                     12 |
| L7n1      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.216647 |                 1.23079 |                             0.110049  |                        0 | diagonal-central |                12 |                     12 |
| L6a5      |                 | -+-          |                 1 | pair-linking-sector-resolved |                     0.227192 |                 1.70755 |                             0.146091  |                        0 | diagonal-central |                18 |                     18 |
| L5a1      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.233965 |                 1.33691 |                             0.124812  |                        0 | diagonal-central |                12 |                     12 |
| L7a6      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.248857 |                 2.2958  |                             0.200253  |                        0 | diagonal-central |                12 |                     12 |
| L7n2      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.251051 |                 1.01788 |                             0.0880323 |                        0 | diagonal-central |                12 |                     12 |

## Pairwise-linking insufficiency flags

| link_id   | common_name     |   components | higher_linking_required   | higher_linking_computed   |
|:----------|:----------------|-------------:|:--------------------------|:--------------------------|
| L6a4      | Borromean rings |            3 | True                      | False                     |
| L7a1      |                 |            2 | True                      | False                     |
| L5a1      |                 |            2 | True                      | False                     |
| L7n2      |                 |            2 | True                      | False                     |
| L7a3      |                 |            2 | True                      | False                     |
| L7a4      |                 |            2 | True                      | False                     |

## v0.3.3 interpretation rules

- Topology uses an independent higher-resolution sampling grid.
- Every 2^m circulation assignment is retained; candidate automorphisms do not quotient sectors.
- Energy terms use preregistered fixed reference scales rather than per-sector baselines.
- `spectrally_stable_claim=true` is possible only with a full off-diagonal Hessian.
- L6a4 is catalogued as the Borromean rings; its Milnor triple invariant is not computed here.