# Full Archive Conclusions

Analyzed datasets in this campaign: **16** of inventory **127**.

## Classification by topology class

| class | N | PASS | FAIL | median growth |
|---|---:|---:|---:|---:|
| knot | 11 | 0 | 11 | 0.326383 |
| link | 4 | 1 | 3 | 0.0771981 |
| torus_knot | 1 | 0 | 1 | 0.359241 |

## Gate failure counts

| gate | FAIL count |
|---|---:|
| P5_short_ringdown_bounded | 15 |
| P4_TBK_collective_stabilizes | 13 |
| P2_linear_growth_bounded | 11 |
| P7_RPO_recurrence | 6 |
| P3_nearest_relevant_separates | 5 |
| P1_jacobian_converged | 2 |

## Lowest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| knotplot:link_8.2.1 | 0.03746126 | FAIL |
| knotplot:link_7.2.5 | 0.06353249 | FAIL |
| knotplot:link_4.2.1 | 0.09086371 | PASS |
| fremlin:10_1:knot.10_1n | 0.1076091 | FAIL |
| knotplot:knot_10.1 | 0.1174573 | FAIL |
| fremlin:7_5:knot.7_5 | 0.1240151 | FAIL |
| knotplot:link_6.2.1 | 0.1940691 | FAIL |
| fremlin:8_7:knot.8_7s | 0.2609757 | FAIL |
| fremlin:5_2:knot.5_2d | 0.3081807 | FAIL |
| fremlin:4_1:knot.4_1 | 0.3263827 | FAIL |
| fremlin:8_11:knot.8_11 | 0.3352968 | FAIL |
| knotplot:torus_2.7 | 0.359241 | FAIL |
| fremlin:7_1:knot.7_1 | 0.3620083 | FAIL |
| fremlin:8_3:knot.8_3d | 0.4417902 | FAIL |
| fremlin:8_19:knot.8_19u | 0.8791565 | FAIL |
| fremlin:8_15:knot.8_15 | 1 | FAIL |

## Highest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:8_15:knot.8_15 | 1 | FAIL |
| fremlin:8_19:knot.8_19u | 0.8791565 | FAIL |
| fremlin:8_3:knot.8_3d | 0.4417902 | FAIL |
| fremlin:7_1:knot.7_1 | 0.3620083 | FAIL |
| knotplot:torus_2.7 | 0.359241 | FAIL |
| fremlin:8_11:knot.8_11 | 0.3352968 | FAIL |
| fremlin:4_1:knot.4_1 | 0.3263827 | FAIL |
| fremlin:5_2:knot.5_2d | 0.3081807 | FAIL |
| fremlin:8_7:knot.8_7s | 0.2609757 | FAIL |
| knotplot:link_6.2.1 | 0.1940691 | FAIL |
| fremlin:7_5:knot.7_5 | 0.1240151 | FAIL |
| knotplot:knot_10.1 | 0.1174573 | FAIL |
| fremlin:10_1:knot.10_1n | 0.1076091 | FAIL |
| knotplot:link_4.2.1 | 0.09086371 | PASS |
| knotplot:link_7.2.5 | 0.06353249 | FAIL |
| knotplot:link_8.2.1 | 0.03746126 | FAIL |

## Representation sensitivity

Canonical topology groups with more than one Fremlin/KnotPlot representation are shown; spread is descriptive and does not change gates.

| canonical | N | min growth | max growth | spread |
|---|---:|---:|---:|---:|
| 10_1 | 2 | 0.107609 | 0.117457 | 0.00984824 |

## RPO candidates

No valid excursion-and-return RPO candidate in this campaign.

## Guardrails

- PASS/FAIL remains per-dataset and basis-dependent.
- RPO/Floquet is evaluated only for datasets passing the preregistered linear-growth precondition in EXTRA_EXTENDED/FULL.
- All Fremlin variants are separate inputs; no suffix variant is silently discarded.
- Link pairwise Gauss-linking conservation is monitored without an imposed reconnection operator.
