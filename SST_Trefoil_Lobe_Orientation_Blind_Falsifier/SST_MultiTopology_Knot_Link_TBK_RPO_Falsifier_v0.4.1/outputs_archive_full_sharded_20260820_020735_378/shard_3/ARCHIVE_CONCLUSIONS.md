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
