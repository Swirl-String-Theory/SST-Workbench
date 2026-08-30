# Trefoil Balance Point Campaign v0.2.3

**Overall:** `ZERO_AT_FROZEN_RANGE_BOUNDARY`

## Zero track

| iteration | t* | ΔL/L0 at zero | ΔRg/Rg0 at zero |
|---:|---:|---:|---:|
| 30000 | 1.2689947129 | -0.0020781172 | 0.0020781172 |
| 40000 | 1.2728751618 | -0.0023091357 | 0.0023091357 |
| 50000 | 1.2765067815 | -0.0025256264 | 0.0025256264 |
| 60000 | 1.2799332932 | -0.0027300906 | 0.0027300906 |
| 70000 | 1.2831857616 | -0.0029243197 | 0.0029243197 |
| 80000 | 1.2862878472 | -0.0031096707 | 0.0031096707 |
| 90000 | 1.2892573053 | -0.0032871828 | 0.0032871828 |
| 100000 | 1.2921083273 | -0.0034576811 | 0.0034576811 |
| 120000 | 1.2974990274 | -0.0037801994 | 0.0037801994 |
| 140000 | 1.3025300542 | -0.0040813348 | 0.0040813348 |
| 160000 | 1.3072523065 | -0.0043640763 | 0.0043640763 |
| 180000 | 1.3117044686 | -0.0046307086 | 0.0046307086 |
| 200000 | 1.3159171974 | -0.004883056 | 0.004883056 |

## Late gates

- zero velocity / 10k: `0.0023005377238201428`
- last-3 zero spread: `0.008664890829433114`
- boundary: `True`
- left panel: `False` (None)
- ΔL-at-zero slope /10k: `-0.00013775434777142615`
- ΔRg-at-zero slope /10k: `0.00013775434777142615`
- fixed-E passes: `[]`

## Classification semantics

- `TRUE_GEOMETRIC_FIXED_POINT_CANDIDATE`: zero settles and both separate geometric observables are stationary.
- `SETTLED_COMPENSATING_BALANCE_ZERO`: zero settles but at least one separate observable keeps drifting.
- `MOVING_LATE_BALANCE_ZERO`: zero remains inside the panel but keeps migrating.
- `ZERO_AT_FROZEN_RANGE_BOUNDARY`: crossing is within the frozen boundary margin.
- `ZERO_LEFT_FROZEN_PANEL`: the crossing has moved outside the existing q/h/p panel.
