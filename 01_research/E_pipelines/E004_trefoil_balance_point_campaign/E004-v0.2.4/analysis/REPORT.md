# Trefoil Balance Point Campaign v0.2.4

**Overall:** `MOVING_LATE_BALANCE_ZERO`

## Overlap calibration

- status: **PASS**
- historical zero @200k: `1.3159171973792236`
- regenerated zero @200k: `1.315917185603529`
- absolute difference: `1.1775694641613654e-08`

## Extended zero track

| iteration | t* | ΔL/L0 at zero | ΔRg/Rg0 at zero |
|---:|---:|---:|---:|
| 200000 | 1.3159171856 | -0.0048830556 | 0.0048830556 |
| 220000 | 1.3199163364 | -0.0051226399 | 0.0051226399 |
| 240000 | 1.3237230142 | -0.0053507291 | 0.0053507291 |
| 260000 | 1.3273559083 | -0.0055684289 | 0.0055684289 |
| 280000 | 1.3308310728 | -0.0057766988 | 0.0057766988 |
| 300000 | 1.3341626523 | -0.0059763809 | 0.0059763809 |
| 320000 | 1.3373631319 | -0.0061682213 | 0.0061682213 |
| 340000 | 1.3404436532 | -0.0063528855 | 0.0063528855 |
| 360000 | 1.3434141432 | -0.0065309648 | 0.0065309648 |
| 380000 | 1.3462834596 | -0.0067029909 | 0.0067029909 |
| 400000 | 1.3490595979 | -0.0068694419 | 0.0068694419 |

## Late gates

- zero velocity /10k: `0.0014616369211869402`
- last-three spread: `0.005645454633858016`
- ΔL-at-zero slope /10k: `-8.762732708419418e-05`
- ΔRg-at-zero slope /10k: `8.762732708419418e-05`
- settled: `False`
- individual observables stationary: `False`
- boundary: `False`
- left extended panel: `False` (None)

The overlap gate is a prerequisite: failure there invalidates use of the cold-start extended panel.
