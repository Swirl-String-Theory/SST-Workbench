# SST ideal-link campaign report — v0.2.1

- Links completed: **18**
- Preset: **quick**
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
| L4a1      |                                0.147007 | --                      |          19.9342 |
| L2a1      |                                0.177857 | --                      |          12.5664 |
| L6n1      |                                0.184612 | -+-                     |          25.093  |
| L6a4      |                                0.186292 | ---                     |          29.1466 |
| L7a1      |                                0.212905 | --                      |          33.0249 |
| L6a3      |                                0.217417 | -+                      |          27.0176 |
| L6a5      |                                0.218317 | -+-                     |          28.766  |
| L7n1      |                                0.219872 | --                      |          27.699  |

## Contact-map orbit candidates

| link_id   |   contact_map_closed_orbits |   contact_map_period9_candidates |   contact_cycle_rank |
|:----------|----------------------------:|---------------------------------:|---------------------:|
| L6a3      |                          32 |                                0 |                   79 |
| L7a7      |                          32 |                                0 |                   75 |
| L6a5      |                          18 |                                0 |                   97 |
| L6n1      |                          18 |                                0 |                   43 |
| L7a2      |                          18 |                                0 |                   29 |
| L7a5      |                          17 |                                0 |                   45 |
| L7a4      |                          17 |                                0 |                   42 |
| L6a2      |                          16 |                                0 |                   55 |

## Largest total centerline lengths

| link_id   |   total_length_D |   components |
|:----------|-----------------:|-------------:|
| L7a1      |          33.0249 |            2 |
| L7a7      |          32.9096 |            3 |
| L7a2      |          32.8861 |            2 |
| L7a4      |          32.796  |            2 |
| L7a3      |          32.6445 |            2 |

## Largest pair-linking content

| link_id   |   total_abs_linking |   signed_linking |
|:----------|--------------------:|-----------------:|
| L6a3      |             3.00262 |          3.00262 |
| L6a2      |             3.00242 |         -3.00242 |
| L7a7      |             3.00154 |          1.00027 |
| L6a5      |             3.00129 |          1.00032 |
| L6n1      |             3.0007  |         -1.00022 |

## Output map

- `contact_patches.csv`: clustered self/mutual contact patches
- `contact_map_orbits.csv`: directed jump-and-advance closed contact-map cycles
- `circulation_sign_configurations.csv`: all circulation sectors with primary-epsilon flag
- `convergence.csv`: sampled and locally refined curvature maxima
- `summary.csv`: fixed-core ranking plus legacy epsilon-min diagnostic
- `per_link/*.json`: complete audit ledger