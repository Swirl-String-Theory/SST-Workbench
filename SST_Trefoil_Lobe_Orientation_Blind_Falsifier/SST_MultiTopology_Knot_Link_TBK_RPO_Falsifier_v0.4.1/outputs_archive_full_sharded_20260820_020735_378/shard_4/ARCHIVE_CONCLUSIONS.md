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
