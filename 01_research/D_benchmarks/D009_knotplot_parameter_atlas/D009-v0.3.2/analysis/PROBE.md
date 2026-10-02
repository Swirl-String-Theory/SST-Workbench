# KnotPlot 3.1 Parameter Effect Atlas — PROBE (v0.3.3)

> Preparation/relaxation sensitivity atlas; not a physical Euler stability proof.

Classification uses **uniform-arclength + cyclic-origin + proper-Kabsch RMS**.
The v0.3.2 bead-index RMS is retained only as an audit metric.

| family | category | classification | shape-invariant RMS | legacy indexed RMS |
|---|---|---:|---:|---:|
| mechforce | core_force | **EFFECTIVE_STRONG** | 0.0406799 | 0.0362528 |
| elecforce | core_force | **EFFECTIVE_STRONG** | 0.0145029 | 0.0140046 |
| bendforce | core_force | **NULL_AT_100** | 8.00528e-06 | 7.69051e-06 |
| charge | core_force | **EFFECTIVE_STRONG** | 0.0377256 | 0.0392155 |
| hooke | core_force | **EFFECTIVE_STRONG** | 0.0430145 | 0.0381954 |
| power | core_force | **EFFECTIVE_STRONG** | 0.0933871 | 0.0939084 |
| tinc | numerical | **EFFECTIVE_STRONG** | 0.0133677 | 0.0132656 |
| bencon | core_force | **EFFECTIVE_WEAK** | 3.24737e-05 | 3.11699e-05 |
| bangle | core_force | **NULL_AT_100** | 1.64757e-16 | 2.19781e-16 |
| close | numerical | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| max-dr | numerical | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| dstep | numerical | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| thermalforce | secondary_force | **EFFECTIVE_WEAK** | 0.000989159 | 0.000990432 |
| thfstrength | secondary_force | **EFFECTIVE_MEDIUM** | 0.00450975 | 0.00456711 |
| amechforce | secondary_force | **EFFECTIVE_MEDIUM** | 0.00511938 | 0.00488219 |
| aelecforce | secondary_force | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| amfpower | secondary_force | **EFFECTIVE_STRONG** | 0.0212371 | 0.0207586 |
| aelmag | secondary_force | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| extforce | secondary_force | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| velforce | secondary_force | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| velmag | secondary_force | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| tanforce | secondary_force | **EFFECTIVE_MEDIUM** | 0.00752707 | 0.209164 |
| tanmag | secondary_force | **EFFECTIVE_STRONG** | 0.0190493 | 0.227062 |
| drag | secondary_force | **RUN_FAILED** |  |  |
| dragmag | secondary_force | **RUN_FAILED** |  |  |
| endforce | secondary_force | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| symmforce | secondary_force | **EFFECTIVE_MEDIUM** | 0.00133625 | 0.001423 |
| syfmag | secondary_force | **EFFECTIVE_MEDIUM** | 0.00313169 | 0.00320368 |
| sytmag | secondary_force | **EFFECTIVE_MEDIUM** | 0.00225315 | 0.00219114 |
| syrmag | secondary_force | **EFFECTIVE_MEDIUM** | 0.00223635 | 0.00239644 |
| gravity | secondary_force | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| grastrength | secondary_force | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| cradius | geometry_control | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| bead-radius | geometry_control | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| bradius | geometry_control | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| stusplit | discretization | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| stuthresh | discretization | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| minsplitfactor | discretization | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| spring-length | special_dynamics | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| cent-potential | special_dynamics | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| zforce | special_dynamics | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| Kzforce | special_dynamics | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| fmax | special_dynamics | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| spstr | special_dynamics | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |
| f-d-coupled | special_dynamics | **NULL_AT_100** | 3.46154e-16 | 4.30855e-16 |

## Shape-invariant effect ranking

- `power`: shape=0.0933871; legacy-indexed=0.0939084 — EFFECTIVE_STRONG
- `hooke`: shape=0.0430145; legacy-indexed=0.0381954 — EFFECTIVE_STRONG
- `mechforce`: shape=0.0406799; legacy-indexed=0.0362528 — EFFECTIVE_STRONG
- `charge`: shape=0.0377256; legacy-indexed=0.0392155 — EFFECTIVE_STRONG
- `amfpower`: shape=0.0212371; legacy-indexed=0.0207586 — EFFECTIVE_STRONG
- `tanmag`: shape=0.0190493; legacy-indexed=0.227062 — EFFECTIVE_STRONG
- `elecforce`: shape=0.0145029; legacy-indexed=0.0140046 — EFFECTIVE_STRONG
- `tinc`: shape=0.0133677; legacy-indexed=0.0132656 — EFFECTIVE_STRONG
- `tanforce`: shape=0.00752707; legacy-indexed=0.209164 — EFFECTIVE_MEDIUM
- `amechforce`: shape=0.00511938; legacy-indexed=0.00488219 — EFFECTIVE_MEDIUM
- `thfstrength`: shape=0.00450975; legacy-indexed=0.00456711 — EFFECTIVE_MEDIUM
- `syfmag`: shape=0.00313169; legacy-indexed=0.00320368 — EFFECTIVE_MEDIUM
- `sytmag`: shape=0.00225315; legacy-indexed=0.00219114 — EFFECTIVE_MEDIUM
- `syrmag`: shape=0.00223635; legacy-indexed=0.00239644 — EFFECTIVE_MEDIUM
- `symmforce`: shape=0.00133625; legacy-indexed=0.001423 — EFFECTIVE_MEDIUM
- `thermalforce`: shape=0.000989159; legacy-indexed=0.000990432 — EFFECTIVE_WEAK
- `bencon`: shape=3.24737e-05; legacy-indexed=3.11699e-05 — EFFECTIVE_WEAK
- `bendforce`: shape=8.00528e-06; legacy-indexed=7.69051e-06 — NULL_AT_100
- `zforce`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `velmag`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `velforce`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `stuthresh`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `stusplit`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `spstr`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `spring-length`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `minsplitfactor`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `max-dr`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `gravity`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `grastrength`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `fmax`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `f-d-coupled`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `extforce`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `endforce`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `dstep`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `cradius`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `close`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `cent-potential`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `bradius`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `bead-radius`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `aelmag`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `aelecforce`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `Kzforce`: shape=3.46154e-16; legacy-indexed=4.30855e-16 — NULL_AT_100
- `bangle`: shape=1.64757e-16; legacy-indexed=2.19781e-16 — NULL_AT_100

## Metric audit note

- v0.3.2 paired bead index `i` with bead index `i` after rigid alignment.
- v0.3.3 uniformly resamples both closed curves in arclength and searches all cyclic origins before Kabsch.
- This suppresses false effect inflation from tangential bead redistribution.
- Physical scale differences are deliberately retained.
- Curve traversal reversal is not searched.
