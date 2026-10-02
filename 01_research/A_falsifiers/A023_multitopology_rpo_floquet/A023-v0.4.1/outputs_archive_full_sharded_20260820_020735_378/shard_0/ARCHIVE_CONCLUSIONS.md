# Full Archive Conclusions

Analyzed datasets in this campaign: **16** of inventory **127**.

## Classification by topology class

| class | N | PASS | FAIL | median growth |
|---|---:|---:|---:|---:|
| knot | 13 | 0 | 13 | 0.567688 |
| torus_link | 2 | 0 | 2 | 0.531962 |
| unlink | 1 | 0 | 1 | 0.175794 |

## Gate failure counts

| gate | FAIL count |
|---|---:|
| P4_TBK_collective_stabilizes | 15 |
| P5_short_ringdown_bounded | 15 |
| P2_linear_growth_bounded | 13 |
| P3_nearest_relevant_separates | 8 |
| P7_RPO_recurrence | 3 |
| P1_jacobian_converged | 2 |
| P0_geometry_core_clear | 1 |

## Lowest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| knotplot:knot_7.2 | 0.06483614 | FAIL |
| knotplot:knot_4.1 | 0.08958096 | FAIL |
| fremlin:5_2:knot.5_2 | 0.102469 | FAIL |
| knotplot:link_0.3.1 | 0.1757939 | FAIL |
| knotplot:knot_8.18 | 0.2113154 | FAIL |
| knotplot:torus_2.6 | 0.2330242 | FAIL |
| fremlin:8_19:knot.8_19t | 0.3283098 | FAIL |
| fremlin:8_10:knot.8_10s | 0.3964459 | FAIL |
| fremlin:8_3:knot.8_3 | 0.5676877 | FAIL |
| fremlin:8_7:knot.8_7d | 0.6062184 | FAIL |
| fremlin:3_1:knot.3_1u | 0.7362353 | FAIL |
| fremlin:6_3:knot.6_3z | 0.7961552 | FAIL |
| fremlin:7_4:knot.7_4 | 0.8267514 | FAIL |
| fremlin:10_1:knot.10_1 | 0.8280899 | FAIL |
| knotplot:torus_6.21 | 0.830899 | FAIL |
| fremlin:8_14:knot.8_14r | 0.9442683 | FAIL |

## Highest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:8_14:knot.8_14r | 0.9442683 | FAIL |
| knotplot:torus_6.21 | 0.830899 | FAIL |
| fremlin:10_1:knot.10_1 | 0.8280899 | FAIL |
| fremlin:7_4:knot.7_4 | 0.8267514 | FAIL |
| fremlin:6_3:knot.6_3z | 0.7961552 | FAIL |
| fremlin:3_1:knot.3_1u | 0.7362353 | FAIL |
| fremlin:8_7:knot.8_7d | 0.6062184 | FAIL |
| fremlin:8_3:knot.8_3 | 0.5676877 | FAIL |
| fremlin:8_10:knot.8_10s | 0.3964459 | FAIL |
| fremlin:8_19:knot.8_19t | 0.3283098 | FAIL |
| knotplot:torus_2.6 | 0.2330242 | FAIL |
| knotplot:knot_8.18 | 0.2113154 | FAIL |
| knotplot:link_0.3.1 | 0.1757939 | FAIL |
| fremlin:5_2:knot.5_2 | 0.102469 | FAIL |
| knotplot:knot_4.1 | 0.08958096 | FAIL |
| knotplot:knot_7.2 | 0.06483614 | FAIL |

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
