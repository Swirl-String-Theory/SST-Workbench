# A054 v0.1.1 — Post-reveal analysis (reconstructed semantic reveal)

## Integrity

The blind interpretation was frozen first. `PRE_REVEAL_STATISTICS.json` SHA-256: `49ffda87a545573418e757bfebea29f7444f77cb57e9af29c8a9340daf6ce8ab`.

The original random private mapping is not retained in the BLIND archive. The semantic reveal was therefore reconstructed from exact regenerated `A054-GEOMETRY-SHA256-v1` hashes. 75 candidates match uniquely; 24 candidates form 12 duplicate-geometry pairs. Those pairs differ only in an unused provider partner for homogeneous `000` or `111` cells, so architecture and twist bits remain unambiguous for all 99 candidates.

## Blind prediction -> reveal

| blind cluster | n | reveal | polarity pass |
|---|---:|---|---:|
| U | 33 | unlinked | 2/33 |
| L1 | 33 | Triple-Gear T(3,3) | 33/33 |
| L2 | 33 | Borromean | 33/33 |

The blind structural prediction was exactly correct.

## Skeleton medians

| architecture | rel-eq residual | cross stabilization | anisotropy r6 | shape drift | polarity delta-cross |
|---|---:|---:|---:|---:|---:|
| U | 0.906890 | 0.000441 | 0.672296 | 0.006845 | 0.000063 |
| G | 0.523990 | 0.379679 | 0.451695 | 0.016963 | 0.721322 |
| B | 0.500282 | 0.427807 | 0.441321 | 0.014450 | 0.918807 |

Borromean has lower residual/aniso/shape drift and higher positive opposed-state cross stabilization than Triple-Gear, but its +++ state is also more strongly destabilized.

## 5_2 / 6_1 identity under 2+1 polarity

For Triple-Gear historical mixed compositions, a 6_1 component being the opposed-circulation component has positive cross-stabilization advantage in **23/24** cells. Median advantage: **0.00125868**.

- uud-like 5_2+5_2+6_1: **12/12**, median 0.00118009.
- udd-like 5_2+6_1+6_1: **11/12**, median 0.0012902.

For Borromean the same test is **12/24**, with median -2.44968e-06: no detectable knot-identity preference at this level.

## Important null-control finding

The two unlinked gate passes have delta-cross only 0.000930348 and 0.00201414, versus linked medians G=0.721322 and B=0.918807. They are gate-edge effects, not comparable physical survivors.

## Scientific status

This supports a strong architecture × polarity interaction and a smaller Triple-Gear × 6_1 identity interaction. It does **not** yet establish proton/neutron identity. The next hard gate should be restoring-force/Hessian plus Kelvin/Floquet certification without retuning v0.1.1 after reveal.
