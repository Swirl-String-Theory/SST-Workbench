

# shard_0

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


# shard_1

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


# shard_2

# Full Archive Conclusions

Analyzed datasets in this campaign: **16** of inventory **127**.

## Classification by topology class

| class | N | PASS | FAIL | median growth |
|---|---:|---:|---:|---:|
| knot | 14 | 0 | 14 | 0.325912 |
| link | 1 | 0 | 1 | 0.0861379 |
| torus_link | 1 | 0 | 1 | 0.261486 |

## Gate failure counts

| gate | FAIL count |
|---|---:|
| P5_short_ringdown_bounded | 16 |
| P4_TBK_collective_stabilizes | 15 |
| P2_linear_growth_bounded | 13 |
| P3_nearest_relevant_separates | 6 |
| P1_jacobian_converged | 4 |
| P7_RPO_recurrence | 3 |

## Lowest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:12a_1202:knot.12a_1202 | 0.06923167 | FAIL |
| knotplot:link_7.2.6 | 0.08613793 | FAIL |
| knotplot:knot_6.3 | 0.1199276 | FAIL |
| knotplot:knot_5.1 | 0.2174075 | FAIL |
| fremlin:8_11:knot.8_11d | 0.2496629 | FAIL |
| fremlin:8_2:knot.8_2 | 0.2523194 | FAIL |
| knotplot:torus_2.8 | 0.2614859 | FAIL |
| knotplot:knot_9.1 | 0.2979557 | FAIL |
| knotplot:knot_10.123 | 0.3071567 | FAIL |
| fremlin:8_8:knot.8_8d | 0.3446671 | FAIL |
| fremlin:7_5:knot.7_5d | 0.4357959 | FAIL |
| fremlin:8_3:knot.8_3z | 0.4452572 | FAIL |
| fremlin:7_1:knot.7_1p | 0.534463 | FAIL |
| fremlin:4_1:knot.4_1d | 0.5959987 | FAIL |
| fremlin:5_2:knot.5_2r | 0.6459547 | FAIL |
| fremlin:8_15:knot.8_15d | 1 | FAIL |

## Highest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:8_15:knot.8_15d | 1 | FAIL |
| fremlin:5_2:knot.5_2r | 0.6459547 | FAIL |
| fremlin:4_1:knot.4_1d | 0.5959987 | FAIL |
| fremlin:7_1:knot.7_1p | 0.534463 | FAIL |
| fremlin:8_3:knot.8_3z | 0.4452572 | FAIL |
| fremlin:7_5:knot.7_5d | 0.4357959 | FAIL |
| fremlin:8_8:knot.8_8d | 0.3446671 | FAIL |
| knotplot:knot_10.123 | 0.3071567 | FAIL |
| knotplot:knot_9.1 | 0.2979557 | FAIL |
| knotplot:torus_2.8 | 0.2614859 | FAIL |
| fremlin:8_2:knot.8_2 | 0.2523194 | FAIL |
| fremlin:8_11:knot.8_11d | 0.2496629 | FAIL |
| knotplot:knot_5.1 | 0.2174075 | FAIL |
| knotplot:knot_6.3 | 0.1199276 | FAIL |
| knotplot:link_7.2.6 | 0.08613793 | FAIL |
| fremlin:12a_1202:knot.12a_1202 | 0.06923167 | FAIL |

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


# shard_3

# Full Archive Conclusions

Analyzed datasets in this campaign: **16** of inventory **127**.

## Classification by topology class

| class | N | PASS | FAIL | median growth |
|---|---:|---:|---:|---:|
| knot | 12 | 0 | 12 | 0.439195 |
| link | 2 | 0 | 2 | 0.152335 |
| torus_knot | 2 | 0 | 2 | 0.382058 |

## Gate failure counts

| gate | FAIL count |
|---|---:|
| P4_TBK_collective_stabilizes | 16 |
| P5_short_ringdown_bounded | 16 |
| P2_linear_growth_bounded | 13 |
| P3_nearest_relevant_separates | 7 |
| P7_RPO_recurrence | 3 |
| P1_jacobian_converged | 3 |

## Lowest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| knotplot:knot_5.2 | 0.04126677 | FAIL |
| fremlin:7_2:knot.7_2 | 0.08629533 | FAIL |
| knotplot:link_6.3.1 | 0.1141293 | FAIL |
| knotplot:knot_9.2 | 0.1661817 | FAIL |
| fremlin:8_12:knot.8_12d | 0.1776533 | FAIL |
| knotplot:link_7.2.8 | 0.19054 | FAIL |
| fremlin:6_1:knot.6_1 | 0.1997339 | FAIL |
| knotplot:torus_2.9 | 0.2979783 | FAIL |
| fremlin:12a_1202:knot.12a_1202z6 | 0.3420181 | FAIL |
| knotplot:torus_2.11 | 0.4661374 | FAIL |
| fremlin:7_6:knot.7_6d | 0.5363729 | FAIL |
| fremlin:8_15:knot.8_15p | 0.5789257 | FAIL |
| fremlin:4_1:knot.4_1p | 0.8626543 | FAIL |
| fremlin:8_4:knot.8_4 | 1 | FAIL |
| fremlin:8_9:knot.8_9d | 1 | FAIL |
| fremlin:8_2:knot.8_2d | 1 | FAIL |

## Highest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:8_2:knot.8_2d | 1 | FAIL |
| fremlin:8_9:knot.8_9d | 1 | FAIL |
| fremlin:8_4:knot.8_4 | 1 | FAIL |
| fremlin:4_1:knot.4_1p | 0.8626543 | FAIL |
| fremlin:8_15:knot.8_15p | 0.5789257 | FAIL |
| fremlin:7_6:knot.7_6d | 0.5363729 | FAIL |
| knotplot:torus_2.11 | 0.4661374 | FAIL |
| fremlin:12a_1202:knot.12a_1202z6 | 0.3420181 | FAIL |
| knotplot:torus_2.9 | 0.2979783 | FAIL |
| fremlin:6_1:knot.6_1 | 0.1997339 | FAIL |
| knotplot:link_7.2.8 | 0.19054 | FAIL |
| fremlin:8_12:knot.8_12d | 0.1776533 | FAIL |
| knotplot:knot_9.2 | 0.1661817 | FAIL |
| knotplot:link_6.3.1 | 0.1141293 | FAIL |
| fremlin:7_2:knot.7_2 | 0.08629533 | FAIL |
| knotplot:knot_5.2 | 0.04126677 | FAIL |

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


# shard_4

# Full Archive Conclusions

Analyzed datasets in this campaign: **16** of inventory **127**.

## Classification by topology class

| class | N | PASS | FAIL | median growth |
|---|---:|---:|---:|---:|
| knot | 12 | 0 | 12 | 0.453822 |
| link | 4 | 1 | 3 | 0.0601065 |

## Gate failure counts

| gate | FAIL count |
|---|---:|
| P4_TBK_collective_stabilizes | 15 |
| P5_short_ringdown_bounded | 14 |
| P2_linear_growth_bounded | 11 |
| P3_nearest_relevant_separates | 8 |
| P7_RPO_recurrence | 6 |
| P1_jacobian_converged | 3 |

## Lowest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:15331:knot.15331 | 0.04069542 | FAIL |
| knotplot:link_5.2.1 | 0.05120228 | FAIL |
| knotplot:link_2.2.1 | 0.05753888 | PASS |
| knotplot:link_9.2.20 | 0.06267405 | FAIL |
| knotplot:link_6.3.2 | 0.06852997 | FAIL |
| knotplot:knot_7.3 | 0.1258402 | FAIL |
| fremlin:6_2:knot.6_2 | 0.1698027 | FAIL |
| knotplot:knot_3.1 | 0.1747168 | FAIL |
| fremlin:8_16:knot.8_16 | 0.3091157 | FAIL |
| fremlin:7_6:knot.7_6s | 0.3938554 | FAIL |
| fremlin:4_1:knot.4_1z | 0.5137889 | FAIL |
| fremlin:7_2:knot.7_2d | 0.8474637 | FAIL |
| fremlin:8_12:knot.8_12z | 1 | FAIL |
| fremlin:8_20:knot.8_20r | 1 | FAIL |
| fremlin:8_4:knot.8_4d | 1 | FAIL |
| fremlin:9_2:knot.9_2 | 1 | FAIL |

## Highest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:9_2:knot.9_2 | 1 | FAIL |
| fremlin:8_4:knot.8_4d | 1 | FAIL |
| fremlin:8_20:knot.8_20r | 1 | FAIL |
| fremlin:8_12:knot.8_12z | 1 | FAIL |
| fremlin:7_2:knot.7_2d | 0.8474637 | FAIL |
| fremlin:4_1:knot.4_1z | 0.5137889 | FAIL |
| fremlin:7_6:knot.7_6s | 0.3938554 | FAIL |
| fremlin:8_16:knot.8_16 | 0.3091157 | FAIL |
| knotplot:knot_3.1 | 0.1747168 | FAIL |
| fremlin:6_2:knot.6_2 | 0.1698027 | FAIL |
| knotplot:knot_7.3 | 0.1258402 | FAIL |
| knotplot:link_6.3.2 | 0.06852997 | FAIL |
| knotplot:link_9.2.20 | 0.06267405 | FAIL |
| knotplot:link_2.2.1 | 0.05753888 | PASS |
| knotplot:link_5.2.1 | 0.05120228 | FAIL |
| fremlin:15331:knot.15331 | 0.04069542 | FAIL |

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


# shard_5

# Full Archive Conclusions

Analyzed datasets in this campaign: **16** of inventory **127**.

## Classification by topology class

| class | N | PASS | FAIL | median growth |
|---|---:|---:|---:|---:|
| knot | 11 | 0 | 11 | 0.354325 |
| link | 2 | 0 | 2 | 0.0610166 |
| torus_knot | 1 | 0 | 1 | 0.179139 |
| torus_link | 1 | 0 | 1 | 0.119353 |
| unknot | 1 | 0 | 1 | 0.319943 |

## Gate failure counts

| gate | FAIL count |
|---|---:|
| P4_TBK_collective_stabilizes | 15 |
| P5_short_ringdown_bounded | 14 |
| P2_linear_growth_bounded | 11 |
| P3_nearest_relevant_separates | 9 |
| P7_RPO_recurrence | 6 |
| P1_jacobian_converged | 2 |

## Lowest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| knotplot:knot_7.4 | 0.05197524 | FAIL |
| knotplot:link_9.2.40 | 0.05714647 | FAIL |
| knotplot:link_6.3.3 | 0.06488668 | FAIL |
| knotplot:knot_6.1 | 0.1117938 | FAIL |
| knotplot:torus_3.3 | 0.1193527 | FAIL |
| fremlin:9_2:knot.9_2n | 0.1207215 | FAIL |
| knotplot:torus_2.3 | 0.179139 | FAIL |
| fremlin:8_17:knot.8_17 | 0.3088566 | FAIL |
| fremlin:1_1:knot.1_1 | 0.3199434 | FAIL |
| fremlin:6_2:knot.6_2d | 0.3342869 | FAIL |
| fremlin:5_1:knot.5_1 | 0.3543253 | FAIL |
| fremlin:8_5:knot.8_5 | 0.4294541 | FAIL |
| fremlin:7_2:knot.7_2r | 0.5513175 | FAIL |
| fremlin:7_7:knot.7_7d | 0.8515181 | FAIL |
| fremlin:8_21:knot.8_21d | 1 | FAIL |
| fremlin:8_13:knot.8_13d | 1 | FAIL |

## Highest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:8_13:knot.8_13d | 1 | FAIL |
| fremlin:8_21:knot.8_21d | 1 | FAIL |
| fremlin:7_7:knot.7_7d | 0.8515181 | FAIL |
| fremlin:7_2:knot.7_2r | 0.5513175 | FAIL |
| fremlin:8_5:knot.8_5 | 0.4294541 | FAIL |
| fremlin:5_1:knot.5_1 | 0.3543253 | FAIL |
| fremlin:6_2:knot.6_2d | 0.3342869 | FAIL |
| fremlin:1_1:knot.1_1 | 0.3199434 | FAIL |
| fremlin:8_17:knot.8_17 | 0.3088566 | FAIL |
| knotplot:torus_2.3 | 0.179139 | FAIL |
| fremlin:9_2:knot.9_2n | 0.1207215 | FAIL |
| knotplot:torus_3.3 | 0.1193527 | FAIL |
| knotplot:knot_6.1 | 0.1117938 | FAIL |
| knotplot:link_6.3.3 | 0.06488668 | FAIL |
| knotplot:link_9.2.40 | 0.05714647 | FAIL |
| knotplot:knot_7.4 | 0.05197524 | FAIL |

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


# shard_6

# Full Archive Conclusions

Analyzed datasets in this campaign: **16** of inventory **127**.

## Classification by topology class

| class | N | PASS | FAIL | median growth |
|---|---:|---:|---:|---:|
| knot | 11 | 0 | 11 | 0.35036 |
| torus_link | 4 | 0 | 4 | 0.406944 |
| unknot | 1 | 0 | 1 | 0.319463 |

## Gate failure counts

| gate | FAIL count |
|---|---:|
| P2_linear_growth_bounded | 15 |
| P4_TBK_collective_stabilizes | 14 |
| P5_short_ringdown_bounded | 14 |
| P3_nearest_relevant_separates | 8 |
| P7_RPO_recurrence | 2 |
| P1_jacobian_converged | 2 |
| P0_geometry_core_clear | 1 |

## Lowest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| knotplot:knot_9.35 | 0.08995978 | FAIL |
| knotplot:knot_8.1 | 0.142961 | FAIL |
| knotplot:torus_2.4 | 0.163059 | FAIL |
| fremlin:8_6:knot.8_6 | 0.2161584 | FAIL |
| fremlin:7_3:knot.7_3 | 0.2352022 | FAIL |
| fremlin:3_1:knot.3_1 | 0.2574379 | FAIL |
| knotplot:knot_0.1 | 0.3194632 | FAIL |
| fremlin:5_1:knot.5_1p | 0.3503604 | FAIL |
| knotplot:torus_6.9 | 0.3850356 | FAIL |
| fremlin:6_2:knot.6_2p | 0.4158595 | FAIL |
| knotplot:torus_3.6 | 0.4288525 | FAIL |
| fremlin:8_1:knot.8_1 | 0.4713272 | FAIL |
| fremlin:8_18:knot.8_18 | 0.4937873 | FAIL |
| knotplot:torus_6.15 | 0.523461 | FAIL |
| fremlin:8_21:knot.8_21p | 0.8725302 | FAIL |
| fremlin:8_13:knot.8_13p | 0.9766966 | FAIL |

## Highest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:8_13:knot.8_13p | 0.9766966 | FAIL |
| fremlin:8_21:knot.8_21p | 0.8725302 | FAIL |
| knotplot:torus_6.15 | 0.523461 | FAIL |
| fremlin:8_18:knot.8_18 | 0.4937873 | FAIL |
| fremlin:8_1:knot.8_1 | 0.4713272 | FAIL |
| knotplot:torus_3.6 | 0.4288525 | FAIL |
| fremlin:6_2:knot.6_2p | 0.4158595 | FAIL |
| knotplot:torus_6.9 | 0.3850356 | FAIL |
| fremlin:5_1:knot.5_1p | 0.3503604 | FAIL |
| knotplot:knot_0.1 | 0.3194632 | FAIL |
| fremlin:3_1:knot.3_1 | 0.2574379 | FAIL |
| fremlin:7_3:knot.7_3 | 0.2352022 | FAIL |
| fremlin:8_6:knot.8_6 | 0.2161584 | FAIL |
| knotplot:torus_2.4 | 0.163059 | FAIL |
| knotplot:knot_8.1 | 0.142961 | FAIL |
| knotplot:knot_9.35 | 0.08995978 | FAIL |

## Representation sensitivity

Canonical topology groups with more than one Fremlin/KnotPlot representation are shown; spread is descriptive and does not change gates.

| canonical | N | min growth | max growth | spread |
|---|---:|---:|---:|---:|
| 8_1 | 2 | 0.142961 | 0.471327 | 0.328366 |

## RPO candidates

No valid excursion-and-return RPO candidate in this campaign.

## Guardrails

- PASS/FAIL remains per-dataset and basis-dependent.
- RPO/Floquet is evaluated only for datasets passing the preregistered linear-growth precondition in EXTRA_EXTENDED/FULL.
- All Fremlin variants are separate inputs; no suffix variant is silently discarded.
- Link pairwise Gauss-linking conservation is monitored without an imposed reconnection operator.


# shard_7

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
