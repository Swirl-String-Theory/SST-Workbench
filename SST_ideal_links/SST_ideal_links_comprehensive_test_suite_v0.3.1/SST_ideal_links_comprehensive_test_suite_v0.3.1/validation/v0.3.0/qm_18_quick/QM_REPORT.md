# SST ideal links — QM-readiness campaign v0.3.0

- Links completed: **18**
- Preset: **qm_quick**
- Backend: **cpp**
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Scientific boundary

This campaign does not claim a derivation of quantum mechanics. It asks whether each ideal-link background supports discrete circulation sectors, a reduced quadratic energy, a candidate filament two-form, and a stable linearized Hamiltonian spectrum. Absolute energies still require an independently derived SST action scale and canonical hbar normalization.

## Highest-readiness candidates

| link_id   | best_signs   |   readiness_level | readiness_label                |   relative_equilibrium_score |   primary_gradient_norm |   primary_negative_modes | hessian_scheme   |   symplectic_rank |   symplectic_dimension |   unstable_linear_modes |
|:----------|:-------------|------------------:|:-------------------------------|-----------------------------:|------------------------:|-------------------------:|:-----------------|------------------:|-----------------------:|------------------------:|
| L2a1      | --           |                 2 | classical-background-candidate |                     0.178551 |                0.840307 |                        1 | diagonal-central |                10 |                     10 |                       2 |
| L4a1      | --           |                 1 | topological-sector-ready       |                     0.167737 |                1.74696  |                        0 | diagonal-central |                12 |                     12 |                       0 |
| L6a4      | ---          |                 1 | topological-sector-ready       |                     0.192715 |                1.59484  |                        0 | diagonal-central |                18 |                     18 |                       0 |
| L6n1      | -+-          |                 1 | topological-sector-ready       |                     0.194203 |                1.09945  |                        0 | diagonal-central |                18 |                     18 |                       0 |
| L6a5      | -+-          |                 1 | topological-sector-ready       |                     0.22454  |                1.61754  |                        0 | diagonal-central |                18 |                     18 |                       0 |
| L5a1      | -+           |                 1 | topological-sector-ready       |                     0.237057 |               10.989    |                        0 | diagonal-central |                12 |                     12 |                       0 |
| L7a7      | --+          |                 1 | topological-sector-ready       |                     0.240808 |                6.78574  |                        0 | diagonal-central |                18 |                     18 |                       0 |
| L7n1      | --           |                 1 | topological-sector-ready       |                     0.24413  |                1.92716  |                        0 | diagonal-central |                12 |                     12 |                       0 |
| L7a1      | --           |                 1 | topological-sector-ready       |                     0.258838 |               13.1197   |                        0 | diagonal-central |                12 |                     12 |                       0 |
| L7a6      | --           |                 1 | topological-sector-ready       |                     0.261239 |               15.2986   |                        0 | diagonal-central |                12 |                     12 |                       0 |
| L7a5      | -+           |                 1 | topological-sector-ready       |                     0.279152 |               11.0401   |                        0 | diagonal-central |                12 |                     12 |                       0 |
| L7a3      | --           |                 1 | topological-sector-ready       |                     0.292506 |                8.81346  |                        0 | diagonal-central |                12 |                     12 |                       0 |

## Pairwise-linking insufficiency flags

| link_id   |   components | higher_linking_required   |
|:----------|-------------:|:--------------------------|
| L6a4      |            3 | True                      |

## Output map

- `qm_readiness_summary.csv`: one best-sector row per link
- `topological_quantum_labels.csv`: integer linking form, automorphism proxy, sector count
- `sector_readiness.csv`: every independent circulation sector
- `normal_modes.csv`: dimensionless linear frequencies and ratios
- `candidate_symplectic_forms.csv`: rank/nullity and singular spectrum
- `normal_bundle_holonomy.csv`: geometric frame closure angles
- `per_link/*.json`: complete termwise gradients, Hessians and gate ledgers