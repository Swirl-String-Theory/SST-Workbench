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
