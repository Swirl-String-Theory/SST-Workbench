# A058 v0.3.1 — GUI Dynamics controls and qualification register

**Evidence scope.** The following are values visible in the screenshots supplied on 21 October 2026. They are NOT certified numerical defaults from the `reset all` command, nor an observed runtime state of the historical campaign. The screenshots include separate Dynamics Help and GUI panels, not necessarily one synchronized complete simulator state.

| GUI | Displayed value/state | Source description | Recommended experiment |
|---|---:|---|---|
| `elec` | ON | bead-pair repulsion | switch ablation; `charge`, `power` when enabled |
| `charge` | 15.0 | strength of elec force | single-axis sweep with getter verification |
| `power` | 5.00 | repulsion falls off as 1/r^power, not generally 1/r² | single-axis sweep, vary positive admissible range |
| `mech` | ON | nonlinear neighbour attraction | independent switch ablation |
| `hooke` | 1.00 | scale of mech force | sweep, isolate from `amech` |
| `amech` | OFF | alternative mechanical spring force with rest `spring` | independent ON/OFF *separate* regime; do not turn ON invisibly |
| `spring` | 1.40 | amech rest length | sweep only with amech explicitly enabled |
| `afmpower` | 2.00 | amech force exponent; value 1 linear spring | sweep only with amech enabled |
| `max-dr` | 0.100 | numerical maximum displacement | numerical stability convergence control, not physical force |
| `close` | 0.120 | minimum-approach/collision-sensitive setting in this build | vary only with independent 3D collision/safeness checks |
| `tinc` | 15.0 | displayed time increment label; not yet correlated experimentally with `timeincr` command | run getter and alias test before assuming equivalence |
| `tanf` | ON | tangential force; KnotPlot help explicitly warns of an implementation bug | **exclude from certified research baseline**, optional isolated demonstration only |
| `tanmag` | 9.00 | tangential force magnitude | only test isolated experimental `tanf` mode; invalid for conclusions until bug addressed |
| `velfo` | not shown | velocity-proportional force | **excluded from Damped science**; separate `Undamped` branch only, with initial conditions recorded |
| `grav` | not shown | gravity | fixed OFF for reference campaign; exploratory-only branch |
| `therm` | not shown | random agitation | fixed OFF; otherwise require recorded random seed / replicates |
| `symm` | not shown | approximated Greg Buck symmetric energy force | its own mechanism ablation, not interchangeable with `mech` |
| `No Collide` | not shown | user defines it as the prevention of knot self-intersections | keep prevention active, verify 3D nonadjacent-segment distance and KnotPlot `safe` response |
| `Undamped/Damped` | not shown | undamped carries inertia, damped suppresses bead inertia | stratify by regime; never compare as if same time evolution |
| `dstep` | not shown | display redraw cadence | negative control: geometry must be invariant at matched solver counts |
| `stusplit` | not shown | auto splitting of stuck cylinders | keep fixed until topology-preserving operation verified |

**Important distinction.** `collision fast` is present in frozen source code, but do not equate the string with verified GUI `No Collide` semantics without a runtime check. `No Collide` is intended to keep strands from passing through each other; it does NOT validate topology preservation or exclude tunnelling without a geometric check.

**Anonymous axes.** The old eight `S0..S7` assignments are part of frozen PRIVATE commitments. This document intentionally does not reveal, renumber, guess or remap them. The 9 visible numerical GUI controls are not proof that the old preregistered matrix contained all 9. To extend it, preregister an independent A058 v0.4.0 hypothesis and new freeze, retaining v0.2.9/v0.2.10 evidence unchanged.

## Independent 3D snapshot check

Run `python tools/geometry_safety.py knot_output.xyz --close 0.12 --out scratch_safety.json` for a **single-component, closed, plain 3-column XYZ polyline**. Output is minimum Euclidean distance between *nonadjacent segments*, the culprit pair, and whether the snapshot violates `close`. Even `SNAPSHOT_CLEAR` does not certify no crossing between solver checkpoints. For links, assess all cross-component segment pairs as well; this program intentionally fails outside its single-component scope.
