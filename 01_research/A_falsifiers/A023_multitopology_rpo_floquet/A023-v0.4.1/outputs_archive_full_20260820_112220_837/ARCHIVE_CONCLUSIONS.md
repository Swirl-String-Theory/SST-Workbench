# Full Archive Conclusions

Analyzed datasets in this campaign: **127** of inventory **127**.

## Classification by topology class

| class | N | PASS | FAIL | median growth |
|---|---:|---:|---:|---:|
| knot | 96 | 0 | 96 | 0.352343 |
| link | 13 | 2 | 11 | 0.0648867 |
| torus_knot | 5 | 0 | 5 | 0.297978 |
| torus_link | 9 | 0 | 9 | 0.261486 |
| unknot | 2 | 0 | 2 | 0.319703 |
| unlink | 2 | 0 | 2 | 0.208855 |

## Gate failure counts

| gate | FAIL count |
|---|---:|
| P4_TBK_collective_stabilizes | 117 |
| P5_short_ringdown_bounded | 117 |
| P2_linear_growth_bounded | 101 |
| P3_nearest_relevant_separates | 57 |
| P7_RPO_recurrence | 31 |
| P1_jacobian_converged | 21 |
| P0_geometry_core_clear | 2 |

## Lowest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| knotplot:link_8.2.1 | 0.03746126 | FAIL |
| fremlin:15331:knot.15331 | 0.04069542 | FAIL |
| knotplot:knot_5.2 | 0.04126677 | FAIL |
| knotplot:link_5.2.1 | 0.05120228 | FAIL |
| knotplot:knot_7.4 | 0.05197524 | FAIL |
| knotplot:link_9.2.40 | 0.05714647 | FAIL |
| knotplot:link_2.2.1 | 0.05753888 | PASS |
| knotplot:link_9.2.20 | 0.06267405 | FAIL |
| knotplot:link_7.2.5 | 0.06353249 | FAIL |
| knotplot:knot_7.2 | 0.06483614 | FAIL |
| knotplot:link_6.3.3 | 0.06488668 | FAIL |
| knotplot:link_6.3.2 | 0.06852997 | FAIL |
| fremlin:12a_1202:knot.12a_1202 | 0.06923167 | FAIL |
| knotplot:link_7.2.6 | 0.08613793 | FAIL |
| fremlin:7_2:knot.7_2 | 0.08629533 | FAIL |
| knotplot:knot_4.1 | 0.08958096 | FAIL |
| knotplot:knot_9.35 | 0.08995978 | FAIL |
| knotplot:link_4.2.1 | 0.09086371 | PASS |
| fremlin:5_2:knot.5_2 | 0.102469 | FAIL |
| fremlin:10_1:knot.10_1n | 0.1076091 | FAIL |

## Highest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:9_2:knot.9_2 | 1 | FAIL |
| fremlin:8_4:knot.8_4d | 1 | FAIL |
| fremlin:8_20:knot.8_20r | 1 | FAIL |
| fremlin:8_15:knot.8_15d | 1 | FAIL |
| fremlin:8_15:knot.8_15 | 1 | FAIL |
| fremlin:8_13:knot.8_13d | 1 | FAIL |
| fremlin:5_1:knot.5_1u | 1 | FAIL |
| fremlin:8_14:knot.8_14d | 1 | FAIL |
| fremlin:8_2:knot.8_2d | 1 | FAIL |
| fremlin:8_9:knot.8_9d | 1 | FAIL |
| fremlin:8_4:knot.8_4 | 1 | FAIL |
| fremlin:8_12:knot.8_12z | 1 | FAIL |
| fremlin:8_21:knot.8_21d | 1 | FAIL |
| fremlin:8_21:knot.8_21r | 1 | FAIL |
| fremlin:8_13:knot.8_13p | 0.9766966 | FAIL |
| fremlin:8_14:knot.8_14r | 0.9442683 | FAIL |
| fremlin:8_19:knot.8_19u | 0.8791565 | FAIL |
| fremlin:8_21:knot.8_21p | 0.8725302 | FAIL |
| fremlin:4_1:knot.4_1p | 0.8626543 | FAIL |
| fremlin:7_7:knot.7_7d | 0.8515181 | FAIL |

## Representation sensitivity

Canonical topology groups with more than one Fremlin/KnotPlot representation are shown; spread is descriptive and does not change gates.

| canonical | N | min growth | max growth | spread |
|---|---:|---:|---:|---:|
| 10_1 | 3 | 0.107609 | 0.82809 | 0.720481 |
| 12a_1202 | 2 | 0.0692317 | 0.342018 | 0.272786 |
| 3_1 | 4 | 0.174717 | 0.736235 | 0.561518 |
| 4_1 | 5 | 0.089581 | 0.862654 | 0.773073 |
| 5_1 | 4 | 0.217407 | 1 | 0.782593 |
| 5_2 | 4 | 0.0412668 | 0.645955 | 0.604688 |
| 6_1 | 2 | 0.111794 | 0.199734 | 0.0879401 |
| 6_2 | 4 | 0.1192 | 0.41586 | 0.296659 |
| 6_3 | 3 | 0.119928 | 0.796155 | 0.676228 |
| 7_1 | 3 | 0.202715 | 0.534463 | 0.331748 |
| 7_2 | 4 | 0.0648361 | 0.847464 | 0.782628 |
| 7_3 | 3 | 0.12584 | 0.62772 | 0.50188 |
| 7_4 | 2 | 0.0519752 | 0.826751 | 0.774776 |
| 7_5 | 2 | 0.124015 | 0.435796 | 0.311781 |
| 7_6 | 2 | 0.393855 | 0.536373 | 0.142517 |
| 8_1 | 3 | 0.142961 | 0.471327 | 0.328366 |
| 8_11 | 2 | 0.249663 | 0.335297 | 0.0856339 |
| 8_12 | 2 | 0.177653 | 1 | 0.822347 |
| 8_13 | 2 | 0.976697 | 1 | 0.0233034 |
| 8_14 | 2 | 0.944268 | 1 | 0.0557317 |
| 8_15 | 3 | 0.578926 | 1 | 0.421074 |
| 8_17 | 2 | 0.12065 | 0.308857 | 0.188206 |
| 8_18 | 3 | 0.211315 | 0.493787 | 0.282472 |
| 8_19 | 2 | 0.32831 | 0.879157 | 0.550847 |
| 8_2 | 2 | 0.252319 | 1 | 0.747681 |
| 8_21 | 3 | 0.87253 | 1 | 0.12747 |
| 8_3 | 3 | 0.44179 | 0.567688 | 0.125897 |
| 8_4 | 2 | 1 | 1 | 9.99201e-15 |
| 8_6 | 2 | 0.184364 | 0.216158 | 0.0317946 |
| 8_7 | 2 | 0.260976 | 0.606218 | 0.345243 |
| 9_2 | 3 | 0.120722 | 1 | 0.879278 |

## RPO candidates

No valid excursion-and-return RPO candidate in this campaign.

## Guardrails

- PASS/FAIL remains per-dataset and basis-dependent.
- RPO/Floquet is evaluated only for datasets passing the preregistered linear-growth precondition in EXTRA_EXTENDED/FULL.
- All Fremlin variants are separate inputs; no suffix variant is silently discarded.
- Link pairwise Gauss-linking conservation is monitored without an imposed reconnection operator.
