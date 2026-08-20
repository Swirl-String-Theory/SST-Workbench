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
