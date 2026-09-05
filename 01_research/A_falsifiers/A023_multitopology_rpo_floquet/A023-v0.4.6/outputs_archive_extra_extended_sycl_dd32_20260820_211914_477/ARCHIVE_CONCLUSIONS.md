# Full Archive Conclusions

Analyzed datasets in this campaign: **127** of inventory **127**.

## Classification by topology class

| class | N | PASS | FAIL | median growth |
|---|---:|---:|---:|---:|
| knot | 96 | 0 | 96 | 0.352427 |
| link | 13 | 1 | 12 | 0.0932542 |
| torus_knot | 5 | 0 | 5 | 0.328069 |
| torus_link | 9 | 0 | 9 | 0.324138 |
| unknot | 2 | 0 | 2 | 0.352106 |
| unlink | 2 | 0 | 2 | 0.396142 |

## Gate failure counts

| gate | FAIL count |
|---|---:|
| P4_TBK_collective_stabilizes | 112 |
| P5_short_ringdown_bounded | 111 |
| P2_linear_growth_bounded | 105 |
| P3_nearest_relevant_separates | 75 |
| P7_RPO_recurrence | 33 |
| P1_jacobian_converged | 10 |

## Lowest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:7_1:knot.7_1 | 6.18475e-08 | FAIL |
| knotplot:torus_2.7 | 3.184779e-07 | FAIL |
| fremlin:15331:knot.15331 | 0.01883662 | FAIL |
| knotplot:knot_7.4 | 0.03917382 | FAIL |
| knotplot:link_8.2.1 | 0.056871 | FAIL |
| knotplot:link_2.2.1 | 0.06043544 | PASS |
| knotplot:link_9.2.40 | 0.0776497 | FAIL |
| knotplot:link_5.2.1 | 0.08053167 | FAIL |
| knotplot:link_9.2.20 | 0.08130564 | FAIL |
| knotplot:link_7.2.5 | 0.08201816 | FAIL |
| fremlin:12a_1202:knot.12a_1202 | 0.08528158 | FAIL |
| knotplot:knot_7.2 | 0.08769715 | FAIL |
| knotplot:knot_5.2 | 0.08975157 | FAIL |
| knotplot:link_6.3.3 | 0.09325419 | FAIL |
| fremlin:7_2:knot.7_2 | 0.09344916 | FAIL |
| fremlin:7_5:knot.7_5 | 0.1016278 | FAIL |
| knotplot:knot_4.1 | 0.1021801 | FAIL |
| knotplot:knot_6.1 | 0.1054655 | FAIL |
| knotplot:link_6.3.2 | 0.1056789 | FAIL |
| knotplot:knot_9.35 | 0.1100804 | FAIL |

## Highest normalized-growth candidates

| source | growth | status |
|---|---:|---|
| fremlin:9_2:knot.9_2 | 1 | FAIL |
| fremlin:8_4:knot.8_4d | 1 | FAIL |
| fremlin:8_15:knot.8_15d | 1 | FAIL |
| fremlin:8_14:knot.8_14r | 1 | FAIL |
| fremlin:7_3:knot.7_3d | 1 | FAIL |
| fremlin:5_1:knot.5_1u | 1 | FAIL |
| fremlin:10_1:knot.10_1 | 1 | FAIL |
| fremlin:8_21:knot.8_21p | 1 | FAIL |
| fremlin:8_2:knot.8_2d | 1 | FAIL |
| fremlin:8_21:knot.8_21d | 1 | FAIL |
| fremlin:8_9:knot.8_9d | 1 | FAIL |
| fremlin:8_21:knot.8_21r | 1 | FAIL |
| fremlin:8_15:knot.8_15 | 1 | FAIL |
| fremlin:8_13:knot.8_13d | 1 | FAIL |
| fremlin:8_20:knot.8_20r | 1 | FAIL |
| fremlin:8_12:knot.8_12z | 1 | FAIL |
| fremlin:7_2:knot.7_2d | 1 | FAIL |
| fremlin:8_19:knot.8_19u | 0.9726814 | FAIL |
| knotplot:torus_6.21 | 0.9504432 | FAIL |
| fremlin:3_1:knot.3_1u | 0.9500501 | FAIL |

## Representation sensitivity

Canonical topology groups with more than one Fremlin/KnotPlot representation are shown; spread is descriptive and does not change gates.

| canonical | N | min growth | max growth | spread |
|---|---:|---:|---:|---:|
| 10_1 | 3 | 0.131511 | 1 | 0.868489 |
| 12a_1202 | 2 | 0.0852816 | 0.272279 | 0.186998 |
| 3_1 | 4 | 0.225732 | 0.95005 | 0.724318 |
| 4_1 | 5 | 0.10218 | 0.921748 | 0.819568 |
| 5_1 | 4 | 0.235382 | 1 | 0.764618 |
| 5_2 | 4 | 0.0897516 | 0.536287 | 0.446536 |
| 6_1 | 2 | 0.105466 | 0.190202 | 0.0847365 |
| 6_2 | 4 | 0.125379 | 0.872979 | 0.7476 |
| 6_3 | 3 | 0.14901 | 0.79734 | 0.64833 |
| 7_1 | 3 | 6.18475e-08 | 0.621555 | 0.621555 |
| 7_2 | 4 | 0.0876971 | 1 | 0.912303 |
| 7_3 | 3 | 0.129295 | 1 | 0.870705 |
| 7_4 | 2 | 0.0391738 | 0.685989 | 0.646815 |
| 7_5 | 2 | 0.101628 | 0.290077 | 0.188449 |
| 7_6 | 2 | 0.409793 | 0.410826 | 0.00103294 |
| 8_1 | 3 | 0.119107 | 0.375607 | 0.256501 |
| 8_11 | 2 | 0.226796 | 0.276969 | 0.0501729 |
| 8_12 | 2 | 0.195269 | 1 | 0.804731 |
| 8_13 | 2 | 0.860935 | 1 | 0.139065 |
| 8_14 | 2 | 0.89877 | 1 | 0.10123 |
| 8_15 | 3 | 0.697736 | 1 | 0.302264 |
| 8_17 | 2 | 0.25816 | 0.31911 | 0.0609505 |
| 8_18 | 3 | 0.268047 | 0.480731 | 0.212684 |
| 8_19 | 2 | 0.326904 | 0.972681 | 0.645777 |
| 8_2 | 2 | 0.398266 | 1 | 0.601734 |
| 8_21 | 3 | 1 | 1 | 3.16414e-14 |
| 8_3 | 3 | 0.363177 | 0.377089 | 0.0139119 |
| 8_4 | 2 | 0.820896 | 1 | 0.179104 |
| 8_6 | 2 | 0.176519 | 0.243157 | 0.0666379 |
| 8_7 | 2 | 0.24343 | 0.947078 | 0.703648 |
| 9_2 | 3 | 0.120121 | 1 | 0.879879 |

## RPO candidates

No valid excursion-and-return RPO candidate in this campaign.

## Guardrails

- PASS/FAIL remains per-dataset and basis-dependent.
- RPO/Floquet is evaluated only for datasets passing the preregistered linear-growth precondition in EXTRA_EXTENDED/FULL.
- All Fremlin variants are separate inputs; no suffix variant is silently discarded.
- Link pairwise Gauss-linking conservation is monitored without an imposed reconnection operator.
