# SST ideal links — QM-readiness campaign v0.3.2

- Links completed: **18**
- Preset: **qm_quick**
- Backend: **cpp**
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Scientific boundary

This campaign does not derive quantum mechanics. Quick/diagonal Hessians are screening-only. Pairwise-zero links require higher link invariants even when their catalog identity is known.

## Highest-readiness candidates

| link_id   | common_name     | best_signs   |   readiness_level | readiness_label              |   relative_equilibrium_score |   primary_gradient_norm |   primary_gradient_cancellation_ratio |   primary_negative_modes | hessian_scheme   |   symplectic_rank |   symplectic_dimension |
|:----------|:----------------|:-------------|------------------:|:-----------------------------|-----------------------------:|------------------------:|--------------------------------------:|-------------------------:|:-----------------|------------------:|-----------------------:|
| L4a1      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.167737 |                 3.34546 |                              0.647913 |                        0 | diagonal-central |                12 |                     12 |
| L2a1      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.178551 |                12.1766  |                              0.908074 |                        1 | diagonal-central |                10 |                     10 |
| L6a4      | Borromean rings | -++          |                 1 | pair-linking-sector-resolved |                     0.192333 |                 2.32534 |                              0.563568 |                        0 | diagonal-central |                18 |                     18 |
| L6n1      |                 | -+-          |                 1 | pair-linking-sector-resolved |                     0.194203 |                 2.56775 |                              0.492165 |                        0 | diagonal-central |                18 |                     18 |
| L6a5      |                 | -+-          |                 1 | pair-linking-sector-resolved |                     0.22454  |                 2.55563 |                              0.526861 |                        0 | diagonal-central |                18 |                     18 |
| L5a1      |                 | -+           |                 1 | pair-linking-sector-resolved |                     0.237057 |                 2.31607 |                              0.567627 |                        0 | diagonal-central |                12 |                     12 |
| L7a7      |                 | --+          |                 1 | pair-linking-sector-resolved |                     0.240808 |                 2.73715 |                              0.573004 |                        0 | diagonal-central |                18 |                     18 |
| L7n1      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.24413  |                 3.73644 |                              0.667999 |                        0 | diagonal-central |                12 |                     12 |
| L6a3      |                 | -+           |                 1 | pair-linking-sector-resolved |                     0.257767 |                 1.70137 |                              0.694028 |                        0 | diagonal-central |                12 |                     12 |
| L7a1      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.258838 |                 1.90163 |                              0.542468 |                        0 | diagonal-central |                12 |                     12 |
| L7a6      |                 | --           |                 1 | pair-linking-sector-resolved |                     0.261239 |                 1.4215  |                              0.637542 |                        0 | diagonal-central |                12 |                     12 |
| L7a2      |                 | -+           |                 1 | pair-linking-sector-resolved |                     0.271287 |                 2.10806 |                              0.499332 |                        0 | diagonal-central |                12 |                     12 |

## Pairwise-linking insufficiency flags

| link_id   | common_name     |   components | higher_linking_required   | higher_linking_computed   |
|:----------|:----------------|-------------:|:--------------------------|:--------------------------|
| L6a4      | Borromean rings |            3 | True                      | False                     |
| L5a1      |                 |            2 | True                      | False                     |
| L7a1      |                 |            2 | True                      | False                     |
| L7a3      |                 |            2 | True                      | False                     |
| L7a4      |                 |            2 | True                      | False                     |
| L7n2      |                 |            2 | True                      | False                     |

## v0.3.2 interpretation rules

- Topology uses an independent higher-resolution sampling grid.
- Every 2^m circulation assignment is retained; candidate automorphisms do not quotient sectors.
- Energy terms use preregistered fixed reference scales rather than per-sector baselines.
- `spectrally_stable_claim=true` is possible only with a full off-diagonal Hessian.
- L6a4 is catalogued as the Borromean rings; its Milnor triple invariant is not computed here.