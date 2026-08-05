# SST ideal-link campaign report — v0.2.1

- Links completed: **18**
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
| L4a1      |                                0.158192 | --                      |          20.0106 |
| L2a1      |                                0.1825   | --                      |          12.5664 |
| L6n1      |                                0.195855 | -+-                     |          25.1749 |
| L7a1      |                                0.208734 | --                      |          33.2705 |
| L7n1      |                                0.213773 | --                      |          27.7663 |
| L6a3      |                                0.213869 | -+                      |          27.1816 |
| L6a4      |                                0.222568 | -++                     |          29.0063 |
| L7a2      |                                0.223642 | -+                      |          33.0589 |

## Contact-map orbit candidates

| link_id   |   contact_map_closed_orbits |   contact_map_period9_candidates |   contact_cycle_rank |
|:----------|----------------------------:|---------------------------------:|---------------------:|
| L6a3      |                         154 |                                0 |                  170 |
| L6a5      |                         104 |                                0 |                  264 |
| L6a4      |                          74 |                                0 |                  166 |
| L6a2      |                          62 |                                0 |                  182 |
| L7a7      |                          60 |                                0 |                  166 |
| L6n1      |                          60 |                                0 |                  144 |
| L7a2      |                          58 |                                0 |                   93 |
| L5a1      |                          54 |                                0 |                  130 |

## Largest total centerline lengths

| link_id   |   total_length_D |   components |
|:----------|-----------------:|-------------:|
| L7a1      |          33.2705 |            2 |
| L7a2      |          33.0589 |            2 |
| L7a4      |          33.0371 |            2 |
| L7a7      |          32.976  |            3 |
| L7a3      |          32.5923 |            2 |

## Largest pair-linking content

| link_id   |   total_abs_linking |   signed_linking |
|:----------|--------------------:|-----------------:|
| L6a3      |             3.00037 |          3.00037 |
| L6a2      |             3.00034 |         -3.00034 |
| L7a7      |             3.00022 |          1.00004 |
| L6a5      |             3.00018 |          1.00004 |
| L6n1      |             3.0001  |         -1.00003 |

## Output map

- `contact_patches.csv`: clustered self/mutual contact patches
- `contact_map_orbits.csv`: directed jump-and-advance closed contact-map cycles
- `circulation_sign_configurations.csv`: all circulation sectors with primary-epsilon flag
- `convergence.csv`: sampled and locally refined curvature maxima
- `summary.csv`: fixed-core ranking plus legacy epsilon-min diagnostic
- `per_link/*.json`: complete audit ledger