# SST ideal-link campaign report

- Links completed: **18**
- Preset: **quick**
- Compute backend: **cpp**
- Native parity gate: **PASS**
- Native source hash: `cf225e4b2ee2450bb8594f72781ba71d552ff6d43abf4112e5703d24d53a161e`
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Interpretation boundary

All source geometries use Gilbert's diameter normalization `D=1`. The mathematical ropelength based on tube **radius** is therefore twice the reported total `L/D`. Biot–Savart, contact-cycle, mirror and finite-core quantities remain diagnostics unless independently closed.

## Best normal relative-equilibrium fits

| link_id   |   best_relative_equilibrium_score |   total_length_D |
|:----------|----------------------------------:|-----------------:|
| L4a1      |                          0.147007 |          19.9342 |
| L2a1      |                          0.177857 |          12.5664 |
| L6n1      |                          0.184612 |          25.093  |
| L6a4      |                          0.186292 |          29.1466 |
| L7a1      |                          0.212905 |          33.0249 |

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

- `native_audit.json`: C++/Python parity ledger
- `summary.csv`: one comparative feature row per link
- `components.csv`: component-resolved geometry
- `circulation_sign_configurations.csv`: every circulation assignment and backend
- `mutual_contacts.csv`: refined inter-component distance/contact diagnostics
- `convergence.csv`: resolution ladder
- `per_link/*.json`: complete backend-stamped audit ledger
- `plots/`: rankings, feature correlations and PCA