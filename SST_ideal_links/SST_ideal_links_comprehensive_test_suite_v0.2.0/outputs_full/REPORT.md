# SST ideal-link campaign report

- Links completed: **129**
- Preset: **full**
- Compute backend: **cpp**
- Native parity gate: **PASS**
- Native source hash: `726d570c2aeb7ccfc8c9948384ac3e8ec477bcfa0e40713708669094538be359`
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Interpretation boundary

All source geometries use Gilbert's diameter normalization `D=1`. The mathematical ropelength based on tube **radius** is therefore twice the reported total `L/D`. Biot–Savart, contact-cycle, mirror and finite-core quantities remain diagnostics unless independently closed.

## Best normal relative-equilibrium fits

| link_id   |   best_relative_equilibrium_score |   total_length_D |
|:----------|----------------------------------:|-----------------:|
| L4a1      |                          0.15369  |          20.0106 |
| L8a7      |                          0.177746 |          36.862  |
| L8n3      |                          0.179539 |          30.288  |
| L6n1      |                          0.185893 |          25.1749 |
| L8n6      |                          0.195158 |          32.7362 |

## Largest total centerline lengths

| link_id   |   total_length_D |   components |
|:----------|-----------------:|-------------:|
| L9a19     |          41.5298 |            2 |
| L9a20     |          41.5123 |            2 |
| L9a8      |          41.4579 |            2 |
| L9a43     |          41.4279 |            3 |
| L9a3      |          41.3741 |            2 |

## Largest pair-linking content

| link_id   |   total_abs_linking |   signed_linking |
|:----------|--------------------:|-----------------:|
| L8a12     |             4.00076 |          4.00076 |
| L8a14     |             4.00073 |          4.00073 |
| L8a13     |             4.00073 |          4.00073 |
| L9n19     |             4.00049 |         -4.00049 |
| L9a49     |             4.00046 |          2.00021 |

## Output map

- `native_audit.json`: C++/Python parity ledger
- `summary.csv`: one comparative feature row per link
- `components.csv`: component-resolved geometry
- `circulation_sign_configurations.csv`: every circulation assignment and backend
- `mutual_contacts.csv`: refined inter-component distance/contact diagnostics
- `convergence.csv`: resolution ladder
- `per_link/*.json`: complete backend-stamped audit ledger
- `plots/`: rankings, feature correlations and PCA