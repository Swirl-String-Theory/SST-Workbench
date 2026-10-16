# A058 falsification plan

## Central distinction
KnotPlot relaxation is tested as a **geometry-generation algorithm**. A relaxed embedding is not, by itself, evidence that an SST vortex knot is dynamically self-confined or particle-stable.

## Why this falsifier precedes a new export generation
The historical 50 scripts vary topology and bead count but keep the principal relaxation settings fixed. They therefore cannot measure parameter sensitivity. They also call `save <name>.txt` without explicitly selecting `ascii/raw`, leaving the byte format dependent on KnotPlot's `sformat` state. In addition, the scripts do not explicitly set the documented relaxation commands `charge`, `hooke`, `power`, or `timeincr`; v0.1 therefore records `version` and the complete `parameters` state in every KnotPlot run log before deciding whether those controls require a dedicated v0.2 sweep.

## Campaign hierarchy
1. **Static audit** of all 50 historical scripts.
2. **Smoke**: one anonymous topology, enough cases to verify the runner, dstep null control, force liveness, and basic parameter perturbations.
3. **Pilot**: T00--T05; one same-topology dual-generator pair, one symmetry control, two additional single-component cases, and one multi-component link.
4. **Full/production**: only after the pilot identifies a robust parameter envelope. Do **not** regenerate every historical topology first.

## Primary parameter classes
- mechanism ablations: `mechforce`, `elecforce`, `bendforce` (complete 2x2x2 cube, excluding baseline duplication);
- dynamics/numerics: `max-dr`, `close`, `bencon`, `stusplit`;
- null control: `dstep` (display cadence only);
- discretization: bead-count multipliers 0.5x, 2x, 4x;
- relaxation horizon: checkpoints 0, 250, 1000, 4000, 10000, 15000.

## Decision logic
- G1/G8 can reject the historical export protocol on provenance even if the geometry later proves robust.
- G3--G7 continue regardless of G1/G8 failure so we still learn which replacement settings are defensible.
- A new canonical export generation should explicitly write ASCII geometry plus machine-readable metric logs and hashes.
