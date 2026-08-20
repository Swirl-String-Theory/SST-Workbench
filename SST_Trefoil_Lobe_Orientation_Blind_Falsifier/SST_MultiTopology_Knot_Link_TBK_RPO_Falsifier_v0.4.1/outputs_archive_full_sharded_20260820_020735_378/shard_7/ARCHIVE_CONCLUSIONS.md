# Full Archive Conclusions

Analyzed datasets in this campaign: **15** of inventory **127**.

## Classification by topology class

| class | N | PASS | FAIL | median growth |
|---|---:|---:|---:|---:|
| knot | 12 | 0 | 12 | 0.354579 |
| torus_knot | 1 | 0 | 1 | 0.280334 |
| torus_link | 1 | 0 | 1 | 0.239276 |
| unlink | 1 | 0 | 1 | 0.241916 |

## Gate failure counts

| gate | FAIL count |
|---|---:|
| P2_linear_growth_bounded | 14 |
| P4_TBK_collective_stabilizes | 14 |
| P5_short_ringdown_bounded | 13 |
| P3_nearest_relevant_separates | 6 |
| P1_jacobian_converged | 3 |
| P7_RPO_recurrence | 2 |

## Lowest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| knotplot:knot_6.2 | 0.1192001 | FAIL |
| knotplot:knot_8.17 | 0.1206502 | FAIL |
| fremlin:8_6:knot.8_6p | 0.1843638 | FAIL |
| knotplot:knot_7.1 | 0.2027151 | FAIL |
| knotplot:torus_3.9 | 0.239276 | FAIL |
| knotplot:link_0.2.1 | 0.241916 | FAIL |
| fremlin:8_18:knot.8_18z | 0.2476523 | FAIL |
| fremlin:3_1:knot.3_1p | 0.2618357 | FAIL |
| knotplot:torus_2.5 | 0.2803336 | FAIL |
| fremlin:8_1:knot.8_1d | 0.4473233 | FAIL |
| fremlin:6_3:knot.6_3d | 0.5530545 | FAIL |
| fremlin:7_3:knot.7_3d | 0.6277202 | FAIL |
| fremlin:8_21:knot.8_21r | 1 | FAIL |
| fremlin:8_14:knot.8_14d | 1 | FAIL |
| fremlin:5_1:knot.5_1u | 1 | FAIL |

## Highest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:5_1:knot.5_1u | 1 | FAIL |
| fremlin:8_14:knot.8_14d | 1 | FAIL |
| fremlin:8_21:knot.8_21r | 1 | FAIL |
| fremlin:7_3:knot.7_3d | 0.6277202 | FAIL |
| fremlin:6_3:knot.6_3d | 0.5530545 | FAIL |
| fremlin:8_1:knot.8_1d | 0.4473233 | FAIL |
| knotplot:torus_2.5 | 0.2803336 | FAIL |
| fremlin:3_1:knot.3_1p | 0.2618357 | FAIL |
| fremlin:8_18:knot.8_18z | 0.2476523 | FAIL |
| knotplot:link_0.2.1 | 0.241916 | FAIL |
| knotplot:torus_3.9 | 0.239276 | FAIL |
| knotplot:knot_7.1 | 0.2027151 | FAIL |
| fremlin:8_6:knot.8_6p | 0.1843638 | FAIL |
| knotplot:knot_8.17 | 0.1206502 | FAIL |
| knotplot:knot_6.2 | 0.1192001 | FAIL |

## Representation sensitivity

Canonical topology groups with more than one Fremlin/KnotPlot representation are shown; spread is descriptive and does not change gates.

| canonical | N | min growth | max growth | spread |
|---|---:|---:|---:|---:|

## RPO candidates

No valid excursion-and-return RPO candidate in this campaign.

## Guardrails

- PASS/FAIL remains per-dataset and basis-dependent.
- RPO/Floquet is evaluated only for datasets passing the preregistered linear-growth precondition in EXTRA_EXTENDED/FULL.
- All Fremlin variants are separate inputs; no suffix variant is silently discarded.
- Link pairwise Gauss-linking conservation is monitored without an imposed reconnection operator.
