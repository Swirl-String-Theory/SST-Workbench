# SST ideal-link campaign report

- Links completed: **17**
- Preset: **max**
- Compute backend: **cpp**
- Native parity gate: **PASS**
- Native source hash: `726d570c2aeb7ccfc8c9948384ac3e8ec477bcfa0e40713708669094538be359`
- Input SHA-256: `a7481f263d8f152723277d0301372d86cc664c211ea5a50f01d6ac49b7d335de`

## Interpretation boundary

All source geometries use Gilbert's diameter normalization `D=1`. The mathematical ropelength based on tube **radius** is therefore twice the reported total `L/D`. Biot–Savart, contact-cycle, mirror and finite-core quantities remain diagnostics unless independently closed.

## Best normal relative-equilibrium fits

| link_id   |   best_relative_equilibrium_score |   total_length_D |
|:----------|----------------------------------:|-----------------:|
| L4a1      |                          0.157244 |          20.0106 |
| L6n1      |                          0.18737  |          25.1749 |
| L6a4      |                          0.198865 |          29.0063 |
| L7a1      |                          0.201641 |          33.2705 |
| L7n1      |                          0.205508 |          27.7663 |

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
| L6a3      |             3.00009 |          3.00009 |
| L6a2      |             3.00009 |         -3.00009 |
| L7a7      |             3.00005 |          1.00001 |
| L6a5      |             3.00005 |          1.00001 |
| L6n1      |             3.00002 |         -1.00001 |

## Output map

- `native_audit.json`: C++/Python parity ledger
- `summary.csv`: one comparative feature row per link
- `components.csv`: component-resolved geometry
- `circulation_sign_configurations.csv`: every circulation assignment and backend
- `mutual_contacts.csv`: refined inter-component distance/contact diagnostics
- `convergence.csv`: resolution ladder
- `per_link/*.json`: complete backend-stamped audit ledger
- `plots/`: rankings, feature correlations and PCA