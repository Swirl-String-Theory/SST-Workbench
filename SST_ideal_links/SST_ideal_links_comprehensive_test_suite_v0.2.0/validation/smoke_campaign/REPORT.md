# SST ideal-link campaign report

- Links completed: **3**
- Preset: **smoke**
- Compute backend: **cpp**
- Native parity gate: **PASS**
- Native source hash: `cf225e4b2ee2450bb8594f72781ba71d552ff6d43abf4112e5703d24d53a161e`
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Interpretation boundary

All source geometries use Gilbert's diameter normalization `D=1`. The mathematical ropelength based on tube **radius** is therefore twice the reported total `L/D`. Biot–Savart, contact-cycle, mirror and finite-core quantities remain diagnostics unless independently closed.

## Best normal relative-equilibrium fits

| link_id   |   best_relative_equilibrium_score |   total_length_D |
|:----------|----------------------------------:|-----------------:|
| L2a1      |                          0.176891 |          12.5664 |
| L6a4      |                          0.184241 |          29.1471 |
| L7n2      |                          0.286069 |          28.7594 |

## Largest total centerline lengths

| link_id   |   total_length_D |   components |
|:----------|-----------------:|-------------:|
| L6a4      |          29.1471 |            3 |
| L7n2      |          28.7594 |            2 |
| L2a1      |          12.5664 |            2 |

## Largest pair-linking content

| link_id   |   total_abs_linking |   signed_linking |
|:----------|--------------------:|-----------------:|
| L2a1      |         1.0004      |     -1.0004      |
| L7n2      |         7.05965e-05 |     -7.05965e-05 |
| L6a4      |         1.13199e-08 |      1.05356e-08 |

## Output map

- `native_audit.json`: C++/Python parity ledger
- `summary.csv`: one comparative feature row per link
- `components.csv`: component-resolved geometry
- `circulation_sign_configurations.csv`: every circulation assignment and backend
- `mutual_contacts.csv`: refined inter-component distance/contact diagnostics
- `convergence.csv`: resolution ladder
- `per_link/*.json`: complete backend-stamped audit ledger
- `plots/`: rankings, feature correlations and PCA