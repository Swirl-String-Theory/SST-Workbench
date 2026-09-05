# CHANGELOG v0.3.0

- Replaces ad-hoc individual parameter sweeps with a comprehensive trefoil 3.1
  Parameter Effect Atlas.
- Freezes the target KnotPlot runtime baseline from the supplied parameter dump.
- Uses the actual `tinc` parameter name instead of the obsolete/nonexistent
  `timeincr`.
- Adds core force-law, secondary force, numerical, geometry/discretization, and
  special-dynamics families.
- Explicitly excludes UI/render/export/4-D/catalog-generator parameters from
  dynamics inference while retaining an exclusion inventory.
- Two-stage design: all candidates to i100, all accepted families to i1000.
- Adds Kabsch-normalized effect ranking and a unique downstream geometry manifest.
- Keeps KnotPlot preparation sensitivity separate from true physical vortex-knot
  stability.
