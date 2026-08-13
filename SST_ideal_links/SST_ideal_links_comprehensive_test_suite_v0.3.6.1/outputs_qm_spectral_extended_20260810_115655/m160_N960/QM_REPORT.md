# SST ideal links — QM-readiness campaign v0.3.6.1

- Links completed: **3**
- Preset: **qm_full_filtered_m160**
- Backend: **cpp**
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Scientific boundary

This campaign does not derive quantum mechanics. Quick/diagonal Hessians are screening-only. Pairwise-zero links require higher link invariants even when their catalog identity is known.

## Highest-readiness candidates

| link_id   | common_name     | best_signs   |   readiness_level | readiness_label              |   relative_equilibrium_score |   primary_gradient_norm |   primary_gradient_cancellation_ratio |   primary_negative_modes | hessian_scheme   |   symplectic_rank |   symplectic_dimension |
|:----------|:----------------|:-------------|------------------:|:-----------------------------|-----------------------------:|------------------------:|--------------------------------------:|-------------------------:|:-----------------|------------------:|-----------------------:|
| L4a1      | nan             | --           |                 1 | pair-linking-sector-resolved |                     0.152783 |                 3.96174 |                              0.271463 |                        7 | full-central     |                20 |                     20 |
| L6n1      | nan             | -+-          |                 1 | pair-linking-sector-resolved |                     0.185386 |                 8.95347 |                              0.477047 |                        6 | full-central     |                30 |                     30 |
| L6a4      | Borromean rings | ---          |                 1 | pair-linking-sector-resolved |                     0.197962 |                 9.41257 |                              0.516145 |                        5 | full-central     |                30 |                     30 |

## Pairwise-linking insufficiency flags

| link_id   | common_name     |   components | higher_linking_required   | higher_linking_computed   |
|:----------|:----------------|-------------:|:--------------------------|:--------------------------|
| L6a4      | Borromean rings |            3 | True                      | False                     |

## v0.3.5 interpretation rules

- Topology uses an independent higher-resolution sampling grid.
- Raw Fourier geometry is guarded against sub-Nyquist QM sampling; filtered presets are numerical regularizations only.
- Bending/curvature uses analytic Fourier derivatives for source audits and FFT spectral derivatives for resolved perturbed curves.
- Every 2^m circulation assignment is retained; candidate automorphisms do not quotient sectors.
- Energy terms use preregistered fixed reference scales rather than per-sector baselines.
- `spectrally_stable_claim=true` is possible only with a full off-diagonal Hessian.
- L6a4 is catalogued as the Borromean rings; its Milnor triple invariant is not computed here.