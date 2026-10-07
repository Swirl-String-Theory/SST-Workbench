# A054-v0.3.0 Broad Discovery — Result Summary

## Scope

This campaign deliberately removes the historical assumption that `5_2` and `6_1` must be the constituent knots. It compares all 14 prime knots through seven crossings, four three-component skeleton embeddings, historical mixed `5_2/6_1` controls, unlinked controls, and seven direct source-native links.

## Dominant result: global architecture dominates local knot identity

For the balanced 14-knot × 4-linked-skeleton homogeneous matrix, deterministic two-way sum-of-squares decomposition gives:

| observable | architecture | knot identity | interaction |
|---|---:|---:|---:|
| median relative-equilibrium residual | 99.9965% | 0.00134% | 0.00213% |
| median cross-component stabilization | 99.9716% | 0.02688% | 0.00148% |
| median far-field anisotropy | 99.9997% | 0.000172% | 0.000084% |

These percentages are deterministic effect decomposition within this design, **not population-level inferential statistics**.

At this finite-core static layer, `5_2` and `6_1` are therefore not uniquely selected. Their historical status remains a hypothesis, not a result.

## Homogeneous knot medians across the four linked skeleton embeddings

By median relative-equilibrium residual (lower is better in this diagnostic):

`7_4, 7_1, 5_2, 7_5, 6_3, 6_1, 6_2, 7_2, 7_3, 7_6, 5_1, 4_1, 3_1, 7_7`.

The entire spread is small (~6e-4), so this is **not** a defensible particle ranking.

By median cross-component stabilization, `5_2` is highest, followed closely by `7_1` and `7_5`, but again the knot effect is tiny compared with the skeleton effect.

## Same topology, different embedding: a critical falsifier result

`6^3_3` and `T(3,3)` represent the same `L6n1` link topology but produce materially different model observables in their relaxed source embeddings:

| embedding | median rel-eq | median cross-stabilization | median anisotropy |
|---|---:|---:|---:|
| `6^3_3` | 0.628794 | 0.134845 | 0.524447 |
| `T(3,3)` | 0.581019 | 0.291513 | 0.461006 |

Therefore topology label alone is insufficient for this model. Geometry-provider / relaxed-embedding replication is mandatory.

## Direct torus-link ladder

Stage A gives a monotone trend across the source-native torus links:

| link | median rel-eq | median cross-stabilization | median anisotropy |
|---|---:|---:|---:|
| `T(3,3)` | 0.581019 | 0.291513 | 0.461006 |
| `T(6,9)` | 0.494686 | 0.445774 | 0.448489 |
| `T(6,15)` | 0.431632 | 0.513514 | 0.448660 |
| `T(6,21)` | 0.343959 | 0.600447 | 0.445082 |

This is a discovery correlation only. Intrinsic component-knot complexity and pairwise torus linking increase together, so the present design cannot assign causality to either variable alone.

## Stage B direct-link dynamics

| link | status | median shape drift |
|---|---|---:|
| `6^3_1` | NUMERICALLY_QUALIFIED | 0.015388 |
| `6^3_2` | NUMERICALLY_QUALIFIED | 0.018712 |
| `6^3_3` | NUMERICALLY_QUALIFIED | 0.012809 |
| `T(3,3)` | NUMERICALLY_QUALIFIED | 0.014068 |
| `T(6,9)` | NUMERICALLY_QUALIFIED | 0.047808 |
| `T(6,15)` | NUMERICALLY_QUALIFIED | 0.049524 |
| `T(6,21)` | INCONCLUSIVE_NUMERICAL | 0.037944 |

The static standout `T(6,21)` does **not** yet survive numerical certification because linking-drift did not spatially converge. `T(6,9)` and `T(6,15)` remain qualified at this short-horizon layer.

## Next adversarial gate

The next scientifically justified step is provider/embedding replication, followed by the existing v0.2 restoring-force → Kelvin → nonlinear ringdown → conditional RPO/Floquet certification. In particular, raw/pre-RidgeRunner KnotPlot exports and RidgeRunner-polished embeddings should be treated as separate carriers of the same topology, not as independent physical evidence.
