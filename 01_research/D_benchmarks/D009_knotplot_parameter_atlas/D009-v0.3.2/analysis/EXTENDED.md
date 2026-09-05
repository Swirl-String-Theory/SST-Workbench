# KnotPlot 3.1 Parameter Effect Atlas — EXTENDED (v0.3.3)

> Preparation/relaxation sensitivity atlas; not a physical Euler stability proof.

Classification uses **uniform-arclength + cyclic-origin + proper-Kabsch RMS**.
The v0.3.2 bead-index RMS is retained only as an audit metric.

| family | category | classification | shape-invariant RMS | legacy indexed RMS |
|---|---|---:|---:|---:|
| mechforce | core_force | **EFFECTIVE_STRONG** | 0.0956985 | 0.108949 |
| elecforce | core_force | **EFFECTIVE_STRONG** | 0.113466 | 0.110012 |
| bendforce | core_force | **NULL_AT_1000** | 9.15495e-06 | 9.299e-06 |
| charge | core_force | **EFFECTIVE_STRONG** | 0.141552 | 0.141402 |
| hooke | core_force | **EFFECTIVE_STRONG** | 0.135722 | 0.135835 |
| power | core_force | **EFFECTIVE_STRONG** | 0.377994 | 0.376853 |
| tinc | numerical | **EFFECTIVE_STRONG** | 0.0317469 | 0.0317781 |
| bencon | core_force | **EFFECTIVE_WEAK** | 3.72493e-05 | 3.78343e-05 |
| bangle | core_force | **NULL_AT_1000** | 3.85737e-16 | 4.93693e-16 |
| close | numerical | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| max-dr | numerical | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| dstep | numerical | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| thermalforce | secondary_force | **EFFECTIVE_MEDIUM** | 0.00342842 | 0.00346691 |
| thfstrength | secondary_force | **EFFECTIVE_STRONG** | 0.014182 | 0.0143027 |
| amechforce | secondary_force | **EFFECTIVE_STRONG** | 0.0124061 | 0.0120153 |
| aelecforce | secondary_force | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| amfpower | secondary_force | **EFFECTIVE_STRONG** | 0.0250467 | 0.0255614 |
| aelmag | secondary_force | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| extforce | secondary_force | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| velforce | secondary_force | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| velmag | secondary_force | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| tanforce | secondary_force | **EFFECTIVE_STRONG** | 0.0445533 | 0.761053 |
| tanmag | secondary_force | **EFFECTIVE_STRONG** | 0.0857388 | 0.96241 |
| drag | secondary_force | **NOT_RUN** |  |  |
| dragmag | secondary_force | **NOT_RUN** |  |  |
| endforce | secondary_force | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| symmforce | secondary_force | **EFFECTIVE_MEDIUM** | 0.00420904 | 0.00407389 |
| syfmag | secondary_force | **EFFECTIVE_STRONG** | 0.0145568 | 0.0139827 |
| sytmag | secondary_force | **EFFECTIVE_STRONG** | 0.0138804 | 0.0137749 |
| syrmag | secondary_force | **EFFECTIVE_MEDIUM** | 0.00540954 | 0.00495298 |
| gravity | secondary_force | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| grastrength | secondary_force | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| cradius | geometry_control | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| bead-radius | geometry_control | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| bradius | geometry_control | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| stusplit | discretization | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| stuthresh | discretization | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| minsplitfactor | discretization | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| spring-length | special_dynamics | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| cent-potential | special_dynamics | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| zforce | special_dynamics | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| Kzforce | special_dynamics | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| fmax | special_dynamics | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| spstr | special_dynamics | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |
| f-d-coupled | special_dynamics | **NULL_AT_1000** | 6.83886e-17 | 3.45118e-16 |

## Shape-invariant effect ranking

- `power`: shape=0.377994; legacy-indexed=0.376853 — EFFECTIVE_STRONG
- `charge`: shape=0.141552; legacy-indexed=0.141402 — EFFECTIVE_STRONG
- `hooke`: shape=0.135722; legacy-indexed=0.135835 — EFFECTIVE_STRONG
- `elecforce`: shape=0.113466; legacy-indexed=0.110012 — EFFECTIVE_STRONG
- `mechforce`: shape=0.0956985; legacy-indexed=0.108949 — EFFECTIVE_STRONG
- `tanmag`: shape=0.0857388; legacy-indexed=0.96241 — EFFECTIVE_STRONG
- `tanforce`: shape=0.0445533; legacy-indexed=0.761053 — EFFECTIVE_STRONG
- `tinc`: shape=0.0317469; legacy-indexed=0.0317781 — EFFECTIVE_STRONG
- `amfpower`: shape=0.0250467; legacy-indexed=0.0255614 — EFFECTIVE_STRONG
- `syfmag`: shape=0.0145568; legacy-indexed=0.0139827 — EFFECTIVE_STRONG
- `thfstrength`: shape=0.014182; legacy-indexed=0.0143027 — EFFECTIVE_STRONG
- `sytmag`: shape=0.0138804; legacy-indexed=0.0137749 — EFFECTIVE_STRONG
- `amechforce`: shape=0.0124061; legacy-indexed=0.0120153 — EFFECTIVE_STRONG
- `syrmag`: shape=0.00540954; legacy-indexed=0.00495298 — EFFECTIVE_MEDIUM
- `symmforce`: shape=0.00420904; legacy-indexed=0.00407389 — EFFECTIVE_MEDIUM
- `thermalforce`: shape=0.00342842; legacy-indexed=0.00346691 — EFFECTIVE_MEDIUM
- `bencon`: shape=3.72493e-05; legacy-indexed=3.78343e-05 — EFFECTIVE_WEAK
- `bendforce`: shape=9.15495e-06; legacy-indexed=9.299e-06 — NULL_AT_1000
- `bangle`: shape=3.85737e-16; legacy-indexed=4.93693e-16 — NULL_AT_1000
- `zforce`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `velmag`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `velforce`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `stuthresh`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `stusplit`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `spstr`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `spring-length`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `minsplitfactor`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `max-dr`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `gravity`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `grastrength`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `fmax`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `f-d-coupled`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `extforce`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `endforce`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `dstep`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `cradius`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `close`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `cent-potential`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `bradius`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `bead-radius`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `aelmag`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `aelecforce`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000
- `Kzforce`: shape=6.83886e-17; legacy-indexed=3.45118e-16 — NULL_AT_1000

## Metric audit note

- v0.3.2 paired bead index `i` with bead index `i` after rigid alignment.
- v0.3.3 uniformly resamples both closed curves in arclength and searches all cyclic origins before Kabsch.
- This suppresses false effect inflation from tangential bead redistribution.
- Physical scale differences are deliberately retained.
- Curve traversal reversal is not searched.
