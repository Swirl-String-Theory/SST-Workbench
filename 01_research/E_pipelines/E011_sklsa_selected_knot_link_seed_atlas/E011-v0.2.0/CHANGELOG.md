# Changelog

## v0.2.0

- Replaced the v0.1.x KnotPlot-first raw-directory inventory with an E010-v0.3.1 qualification-ledger consumer.
- Added per-topology admission based on E010 production, identity, geometry and literature hard gates.
- Global E010 `publication_ready_geometry_layer=false` no longer invalidates a selected-subset E011 run; excluded topologies are preserved explicitly and cannot enter downstream consensus.
- Added G1/G2/G3 failure counts and carrier-level literature-gate status to E011 diagnostics.
- Added E010 ZIP input support with selective extraction and parent SHA-256 provenance.
- Added carrier-family availability from E010 `source_matrix.csv`; directory existence is never used as carrier evidence.
- Preserved E010 mirror/independence semantics and prevented mirrors from inflating independent provider counts.
- Added deterministic provider representatives, strict/extended metric consensus and pairwise metric deltas without introducing a composite physical ranking.
- Preserved signed `Wr` and separate `|Wr|` comparison.
- Kept the original 45-topology selected SKLSA scope and optional higher-crossing sentinels.
