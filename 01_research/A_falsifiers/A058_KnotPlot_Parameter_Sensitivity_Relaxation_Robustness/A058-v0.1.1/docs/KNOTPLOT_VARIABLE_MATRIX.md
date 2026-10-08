# KnotPlot variable matrix — A058 v0.1.1

A058 deliberately separates documented relaxation controls from display/export controls.

| class | variable/command | v0.1 action | interpretation |
|---|---|---|---|
| relaxation force | `mechforce`, `elecforce`, `bendforce` | full 2x2x2 ablation cube | mechanism/liveness diagnostic |
| relaxation force | `bencon` | 0.25, 0.5, 1, 2, 4 | bending-force sensitivity |
| numerical/topology safety | `max-dr` | 0.0025, 0.005, 0.01, 0.02, 0.04 | step-size sensitivity; all remain below baseline `close=1` |
| exclusion geometry | `close` | 0.5, 0.75, 1, 1.25 | closest-approach sensitivity |
| stuck-state handling | `stusplit` | 0 vs 1 | algorithmic sensitivity |
| display cadence | `dstep` | 1, 10, 50 | strict negative control; should not alter geometry |
| discretization | bead count | 0.5x, 1x, 2x, 4x | convergence test |
| relaxation horizon | `ago` checkpoints | 0, 250, 1k, 4k, 10k, 15k | plateau test |
| export | `save ... ascii` | explicitly pinned | removes `sformat` ambiguity |
| hidden relaxation defaults | `charge`, `hooke`, `power`, `timeincr` | record via `version` + `parameters` in every run log | baseline discovery; promote to a dedicated sweep if materially different across builds or implicated by v0.1 |
| historical display/surface values | `bradius`, `cradius` | held fixed, recorded | not promoted as dynamics without evidence |

The full KnotPlot state space is much larger than this matrix. v0.1 tests the variables that can plausibly contaminate the historical relaxation/export pipeline without turning the pilot into an uncontrolled parameter search.
