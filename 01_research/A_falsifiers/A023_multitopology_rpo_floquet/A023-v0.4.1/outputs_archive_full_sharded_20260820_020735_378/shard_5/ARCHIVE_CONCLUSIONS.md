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
