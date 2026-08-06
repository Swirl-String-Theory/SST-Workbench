# SST ideal links — QM-readiness campaign v0.3.0

- Links completed: **1**
- Preset: **qm_full**
- Backend: **cpp**
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Scientific boundary

This campaign does not claim a derivation of quantum mechanics. It asks whether each ideal-link background supports discrete circulation sectors, a reduced quadratic energy, a candidate filament two-form, and a stable linearized Hamiltonian spectrum. Absolute energies still require an independently derived SST action scale and canonical hbar normalization.

## Highest-readiness candidates

| link_id   | best_signs   |   readiness_level | readiness_label                |   relative_equilibrium_score |   primary_gradient_norm |   primary_negative_modes | hessian_scheme   |   symplectic_rank |   symplectic_dimension |   unstable_linear_modes |
|:----------|:-------------|------------------:|:-------------------------------|-----------------------------:|------------------------:|-------------------------:|:-----------------|------------------:|-----------------------:|------------------------:|
| L2a1      | --           |                 2 | classical-background-candidate |                     0.177857 |                0.315137 |                        2 | full-central     |                16 |                     18 |                       4 |

## Pairwise-linking insufficiency flags

No three-component pairwise-zero cases were flagged in this selection.

## Output map

- `qm_readiness_summary.csv`: one best-sector row per link
- `topological_quantum_labels.csv`: integer linking form, automorphism proxy, sector count
- `sector_readiness.csv`: every independent circulation sector
- `normal_modes.csv`: dimensionless linear frequencies and ratios
- `candidate_symplectic_forms.csv`: rank/nullity and singular spectrum
- `normal_bundle_holonomy.csv`: geometric frame closure angles
- `per_link/*.json`: complete termwise gradients, Hessians and gate ledgers