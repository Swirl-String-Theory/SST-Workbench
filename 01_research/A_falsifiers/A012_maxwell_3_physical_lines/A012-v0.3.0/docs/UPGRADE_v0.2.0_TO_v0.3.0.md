# Upgrade notes: v0.2.0 -> v0.3.0

The main scientific change is an upstream-boundary change, not just a new metric.

v0.2.0 read `..\..\KnotPlot\knots\final` directly. v0.3.0 no longer has a direct KnotPlot input path. E010 PKLSA-v0.3.x is the sole geometry/provenance admission layer.

New mandatory topology track:

- M6 topological circulation/linking;
- M7 mutual helicity/linking when multicomponent carriers are present;
- exact target comes from E010 polygonal linking;
- dynamical observable comes from independent Maxwell-3 Biot--Savart C++ code.

M1--M3 remain as a PKLSA-anchored finite-core stress surrogate. `reach` is the core radius; `Thi=2*reach` is not used as a radius.

Three profiles are provided:

- `basic`: small representative topology request, at most one carrier/topology;
- `extended`: scans the full PKLSA atlas, one deterministic admitted carrier/topology;
- `certification`: all individually admitted nonduplicate carriers.

The current E010-v0.3.1 global all-topology release is not treated as globally publication-ready. v0.3.0 uses carrier-level fail-closed admission and records the global state separately.
