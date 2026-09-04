# SST ideal-link campaign report — v0.2.1

- Links completed: **1**
- Preset: **full**
- Python executable: `/opt/pyvenv/bin/python`
- Compute backend: **cpp**
- Native parity gate: **PASS**
- Primary comparison core: **epsilon/D = 0.1**
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Interpretation boundary

Gilbert uses diameter normalization `D=1`; standard radius-based ropelength is `2L/D`. The fixed-epsilon relative-equilibrium score is the primary ranking. The minimum over epsilon is retained only as a smoothing diagnostic. Contact-map cycles are not yet specular-billiard proofs.

## Best fixed-core normal relative-equilibrium fits

| link_id   |   fixed_core_relative_equilibrium_score | fixed_core_best_signs   |   total_length_D |
|:----------|----------------------------------------:|:------------------------|-----------------:|
| L2a1      |                                  0.1825 | --                      |          12.5664 |

## Contact-map orbit candidates

| link_id   |   contact_map_closed_orbits |   contact_map_period9_candidates |   contact_cycle_rank |
|:----------|----------------------------:|---------------------------------:|---------------------:|
| L2a1      |                           0 |                                0 |                    0 |

## Largest total centerline lengths

| link_id   |   total_length_D |   components |
|:----------|-----------------:|-------------:|
| L2a1      |          12.5664 |            2 |

## Largest pair-linking content

| link_id   |   total_abs_linking |   signed_linking |
|:----------|--------------------:|-----------------:|
| L2a1      |             1.00003 |         -1.00003 |

## Output map

- `contact_patches.csv`: clustered self/mutual contact patches
- `contact_map_orbits.csv`: directed jump-and-advance closed contact-map cycles
- `circulation_sign_configurations.csv`: all circulation sectors with primary-epsilon flag
- `convergence.csv`: sampled and locally refined curvature maxima
- `summary.csv`: fixed-core ranking plus legacy epsilon-min diagnostic
- `per_link/*.json`: complete audit ledger